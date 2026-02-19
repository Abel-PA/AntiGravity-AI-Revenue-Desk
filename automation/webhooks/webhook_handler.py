import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load credentials
load_dotenv()

from automation.webhooks.google_sheets_logger import RevenueDeskLogger
from automation.utils import validate_address, send_slack_notification
from openai import OpenAI

# Initialize OpenAI Client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
N8N_URL = os.getenv("N8N_WEBHOOK_URL")

def extract_from_transcript(transcript):
    """
    Fallback extraction using AI if Retell's structured data is missing.
    """
    if not transcript:
        return {}
        
    print("🤖 Triggering AI Fallback Extraction from Transcript...")
    
    prompt = f"""
    You are a data extraction assistant. Extract the following from this call transcript:
    1. Customer Name
    2. Service Address
    3. Issue Type (e.g., AC Repair, Plumbing)
    4. Was a booking confirmed? (True/False)
    5. Appointment Time (if mentioned)

    Transcript:
    \"\"\"{transcript}\"\"\"

    Return ONLY a JSON object with keys: "name", "address", "issue", "booked", "appointment_time".
    If a field is missing, use null.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Return JSON only."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ AI Fallback Error: {e}")
        return {}

def process_call_data(call_payload):
    """
    Processes post-call data from Retell AI.
    Features: Filtered Events, Deep Extraction, and AI Fallback.
    """
    call_obj = call_payload.get("call") if isinstance(call_payload.get("call"), dict) else call_payload
    call_id = call_obj.get("call_id") or call_payload.get("call_id")
    transcript = call_obj.get("transcript") or call_payload.get("transcript")
    
    print(f"--- Processing Call: {call_id} ---")
    
    # 1. Standard Extraction (Try Retell's structured fields first)
    analysis = call_obj.get("analysis") or call_obj.get("call_analysis") or call_payload.get("analysis") or {}
    custom_vars = call_obj.get("custom_variables") or call_payload.get("custom_variables") or {}
    analysis.update(custom_vars)
    
    customer_number = call_obj.get("from_number") or call_obj.get("customer_number") or call_payload.get("from_number")
    customer_name = analysis.get("customer_name") or analysis.get("name") or analysis.get("full_name")
    raw_address = analysis.get("address") or analysis.get("service_address") or analysis.get("location")
    issue_type = analysis.get("issue_type") or analysis.get("issue")
    
    booked_raw = analysis.get("booked") or analysis.get("is_booked") or analysis.get("appointment_booked")
    is_booked = True if str(booked_raw).lower() in ["true", "yes", "booked"] else False
    appointment_time = analysis.get("appointment_time") or analysis.get("booking_time")

    # 2. AI FALLBACK: If major fields are missing, extract from transcript ourselves
    if (not customer_name or customer_name == "Unknown") or (not raw_address):
        fallback = extract_from_transcript(transcript)
        if fallback:
            customer_name = customer_name or fallback.get("name") or "Unknown"
            raw_address = raw_address or fallback.get("address") or ""
            issue_type = issue_type or fallback.get("issue") or "unknown"
            # Only override booked if Retell said false but AI sees a booking
            if not is_booked:
                is_booked = fallback.get("booked", False)
            appointment_time = appointment_time or fallback.get("appointment_time")

    # 3. Address Validation
    validated_addr, is_valid, _ = validate_address(raw_address)
    
    if not is_valid and raw_address:
        print(f"⚠️ Warning: Address '{raw_address}' could not be verified.")

    # 4. Final Lead Data Assembly
    lead_data = {
        "call_id": call_id,
        "name": customer_name if customer_name else "Unknown",
        "phone": customer_number,
        "address": validated_addr if is_valid else raw_address,
        "issue": issue_type if issue_type else "unknown",
        "status": "Booked" if is_booked else ("Missed Data" if not raw_address else "Qualified Lead"),
        "est_revenue": 150 if is_booked else 0 
    }
    
    # 5. Log to Google Sheets
    try:
        logger = RevenueDeskLogger() # Fresh session
        logger.log_call(lead_data)
        
        # 6. Send Slack Notification
        status_emoji = "✅" if is_booked else ("📞" if raw_address else "⚠️")
        alert_msg = f"{status_emoji} *New AI Interaction:* {lead_data['name']}\n*Status:* {lead_data['status']}\n*Issue:* {lead_data['issue']}\n*Address:* {lead_data['address']}\n*Call ID:* {call_id}"
        send_slack_notification(alert_msg)

    except Exception as e:
        print(f"❌ Error in Workflow: {e}")
    
    # 7. SMS Confirmation
    if is_booked and appointment_time:
        send_sms_confirmation(customer_number, appointment_time)
        
    # 8. Forward to n8n
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
