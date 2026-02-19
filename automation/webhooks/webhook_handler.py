import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load credentials
load_dotenv()

from automation.webhooks.google_sheets_logger import RevenueDeskLogger
from automation.utils import validate_address, send_slack_notification

# Configuration
N8N_URL = os.getenv("N8N_WEBHOOK_URL")
logger = RevenueDeskLogger()

def process_call_data(call_payload):
    """
    Processes post-call data from Retell AI.
    Bulletproof extraction across nested or flat Retell payloads.
    """
    # 0. Try to find the root 'call' object if Retell nested it
    call_obj = call_payload.get("call") if isinstance(call_payload.get("call"), dict) else call_payload
    
    call_id = call_obj.get("call_id") or call_payload.get("call_id")
    print(f"--- Processing Call: {call_id} ---")
    
    # 1. Extract Structured Data 
    # Try multiple nested locations for analysis
    analysis = (
        call_obj.get("analysis") or 
        call_obj.get("call_analysis") or 
        call_payload.get("analysis") or 
        call_payload.get("call_analysis") or 
        {}
    )
    
    # Also look for data inside a 'transcript_with_summary' or similar if it's there
    custom_vars = (
        call_obj.get("custom_variables") or 
        call_payload.get("custom_variables") or 
        {}
    )
    
    # Merge custom variables into analysis (Higher priority)
    analysis.update(custom_vars)
    
    customer_number = call_obj.get("from_number") or call_obj.get("customer_number") or call_payload.get("from_number")
    
    # 2. Extract Intent/Booking info (handling case-sensitivity or underscores)
    is_booked = analysis.get("booked") or analysis.get("is_booked") or False
    issue_type = analysis.get("issue_type") or analysis.get("issue") or "unknown"
    appointment_time = analysis.get("appointment_time") or analysis.get("booking_time")
    
    # 3. Handle Name and Address
    customer_name = analysis.get("customer_name") or analysis.get("name") or analysis.get("customer") or "Unknown"
    raw_address = analysis.get("address") or analysis.get("service_address") or analysis.get("location") or ""
    
    # 4. Address Validation
    validated_addr, is_valid, _ = validate_address(raw_address)
    
    if not is_valid and raw_address:
        print(f"⚠️ Warning: Address '{raw_address}' could not be precisely verified.")

    # 5. Prepare Lead Data for Sheets
    lead_data = {
        "call_id": call_id,
        "name": customer_name,
        "phone": customer_number,
        "address": validated_addr if is_valid else raw_address,
        "issue": issue_type,
        "status": "Booked" if is_booked else ("Missed Data" if not raw_address else "Qualified Lead"),
        "est_revenue": 150 if is_booked else 0 
    }
    
    # 6. Log to Google Sheets (Bulletproof Init)
    try:
        # Initializing inside the function ensures a fresh, thread-safe session for this request
        logger = RevenueDeskLogger()
        logger.log_call(lead_data)
        
        # 7. Send Slack Notification
        status_emoji = "✅" if is_booked else ("📞" if raw_address else "⚠️")
        alert_msg = f"{status_emoji} *New AI Interaction:* {lead_data['name']}\n*Status:* {lead_data['status']}\n*Issue:* {lead_data['issue']}\n*Address:* {lead_data['address']}\n*Call ID:* {call_id}"
        send_slack_notification(alert_msg)

    except Exception as e:
        print(f"❌ Error in Post-Call Workflow: {e}")
    
    # 8. SMS Confirmation (Twilio)
    if is_booked and appointment_time:
        send_sms_confirmation(customer_number, appointment_time)
        
    # 9. Forward to n8n for additional orchestration
    if N8N_URL:
        try:
            requests.post(N8N_URL, json=lead_data)
        except:
            print("⚠️ n8n webhook failed")

def send_sms_confirmation(phone, time):
    print(f"ACTION: Sending Twilio Confirmation to {phone} for {time}")

if __name__ == "__main__":
    # Sample Test Payload (Mocking Retell Webhook)
    sample_payload = {
        "call_id": "call_123456789",
        "from_number": "+15550199",
        "transcript": "Hello, I need an AC repair. My unit is leaking. Yes tomorrow at 2pm works. My name is John.",
        "analysis": {
            "customer_name": "John Doe",
            "address": "123 Maple St, Austin TX",
            "issue_type": "AC Repair",
            "booked": True,
            "appointment_time": "2024-06-20T14:00:00Z",
            "summary": "Customer called for AC leak. Booked for tomorrow 2pm."
        }
    }
    process_call_data(sample_payload)
