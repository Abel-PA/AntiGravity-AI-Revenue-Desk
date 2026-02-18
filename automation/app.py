from fastapi import FastAPI, Request, BackgroundTasks
import os
import json
from dotenv import load_dotenv

# Import our custom modules
from automation.webhooks.webhook_handler import process_call_data
from automation.webhooks.missed_call_recovery import handle_missed_call
from automation.webhooks.sms_ai_agent import get_ai_sms_response
from automation.utils import send_slack_notification
from twilio.rest import Client

load_dotenv()

app = FastAPI(title="AI Revenue Desk™ Engine")

# Twilio Client for SMS responses
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

@app.get("/")
async def root():
    return {"status": "online", "system": "AI Revenue Desk Engine v1.0"}

@app.post("/webhooks/voice-sync")
async def retell_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives post-call data from Retell AI.
    Syncs to Google Sheets and sends SMS confirmation.
    """
    payload = await request.json()
    background_tasks.add_task(process_call_data, payload)
    return {"message": "Voice data received and processing"}

@app.post("/webhooks/missed-call")
async def missed_call_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Triggered by Twilio StatusCallback for missed/busy calls.
    Sends recovery SMS and Slack alert.
    """
    form_data = await request.form()
    customer_phone = form_data.get("From")
    call_status = form_data.get("CallStatus")
    
    if call_status in ["no-answer", "busy", "failed"]:
        background_tasks.add_task(handle_missed_call, customer_phone)
        return {"message": "Missed call recovery initiated"}
    return {"message": "Call status not eligible for recovery"}

@app.post("/webhooks/sms-agent")
async def sms_agent_webhook(request: Request):
    """
    Handles inbound SMS from Twilio and replies using the AI SMS Agent.
    """
    form_data = await request.form()
    customer_phone = form_data.get("From")
    incoming_msg = form_data.get("Body")
    
    # 1. Get AI Response
    ai_response = get_ai_sms_response(customer_phone, incoming_msg)
    
    # 2. Reply via Twilio
    try:
        twilio_client.messages.create(
            body=ai_response,
            from_=TWILIO_PHONE,
            to=customer_phone
        )
        # 3. Notify Slack of the conversation
        send_slack_notification(f"💬 *AI SMS Conversation* with {customer_phone}\n*User:* {incoming_msg}\n*AI:* {ai_response}")
    except Exception as e:
        print(f"Error sending SMS: {e}")

    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
