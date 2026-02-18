import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load credentials
load_dotenv()

from automation.webhooks.google_sheets_logger import RevenueDeskLogger
from automation.utils import validate_address

# Configuration
N8N_URL = os.getenv("N8N_WEBHOOK_URL")
logger = RevenueDeskLogger()

def process_call_data(call_payload):
    """
    Processes post-call data from Retell AI.
    Extracts summary, intent, and customer details.
    """
    print(f"--- Processing Call: {call_payload.get('call_id')} ---")
    
    # 1. Extract Structured Data from Retell Webhook
    analysis = call_payload.get("analysis", {})
    customer_number = call_payload.get("from_number")
    
    # 2. Extract Intent/Booking info
    is_booked = analysis.get("booked", False)
    issue_type = analysis.get("issue_type", "unknown")
    appointment_time = analysis.get("appointment_time", None)
    
    # 3. Address Validation
    raw_address = analysis.get("address", "")
    validated_addr, is_valid, _ = validate_address(raw_address)
    
    if not is_valid:
        print(f"⚠️ Warning: Address '{raw_address}' could not be precisely verified.")

    # 4. Prepare Lead Data for Sheets
    lead_data = {
        "call_id": call_payload.get("call_id"),
        "name": analysis.get("customer_name", "Unknown"),
        "phone": customer_number,
        "address": validated_addr,
        "issue": issue_type,
        "status": "Booked" if is_booked else ("Invalid Address" if not is_valid else "Qualified Lead"),
        "est_revenue": 150 if is_booked else 0 
    }
    
    # 4. Log to Google Sheets (The "CRM" replacement)
    logger.log_call(lead_data)
    
    # 5. SMS Confirmation (Twilio)
    if is_booked and appointment_time:
        send_sms_confirmation(customer_number, appointment_time)
        
    # 6. Forward to n8n for additional orchestration
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
