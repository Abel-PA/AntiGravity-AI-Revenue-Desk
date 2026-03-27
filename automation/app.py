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
    Filter for 'call_analyzed' to prevent duplicate Slack/Sheets events.
    """
    payload = await request.json()
    event_type = payload.get("event")
    
    print(f"DEBUG: Received Retell Webhook - Event: {event_type}")
    
    # Only process when the call is analyzed (has the variables we need)
    if event_type == "call_analyzed":
        print("DEBUG: Processing Analyze Event...")
        background_tasks.add_task(process_call_data, payload)
    else:
        print(f"DEBUG: Skipping event type: {event_type}")

    return {"message": "Webhook received"}

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


@app.post("/voice/incoming")
async def voice_incoming(request: Request):
    """
    Rings the real phone for 10 seconds.
    If no answer, Twilio hits /voice/dial-result with status.
    """
    from fastapi.responses import Response
    
    # Construct base URL dynamically for Railway
    base_url = str(request.base_url).rstrip("/")
    if "up.railway.app" in base_url and base_url.startswith("http://"):
        base_url = base_url.replace("http://", "https://")
        
    action_url = f"{base_url}/voice/dial-result"
    real_phone = os.getenv("REAL_MOBILE_NUMBER", "+17176780349")
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial timeout="10" answerOnBridge="true" action="{action_url}" method="POST">
    <Number>{real_phone}</Number>
  </Dial>
</Response>"""
    return Response(content=twiml, media_type="text/xml")

@app.post("/voice/dial-result")
async def voice_dial_result(request: Request):
    """
    Checks the status of the dial attempt. If not answered, connect to AI agent.
    """
    from fastapi.responses import Response
    
    form_data = await request.form()
    status = form_data.get("DialCallStatus", "failed")
    
    # Send empty response if answered
    if status == 'answered':
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="text/xml")
        
    # Trigger Retell AI Agent Fallback via their SIP Trunk
    if status in ['no-answer', 'busy', 'failed', 'canceled']:
        # Extract the original Twilio number that the customer called
        to_number = form_data.get("To", "").replace("+", "")
        if not to_number:
             to_number = "unknown"
             
        # Create the Retell SIP routing URI dynamically using the number Retell knows about
        ai_sip_uri = os.getenv("AI_AGENT_INBOUND_URL", f"sip:{to_number}@sip.retellai.com;transport=tcp")
        
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Sip>{ai_sip_uri}</Sip>
  </Dial>
</Response>"""
        return Response(content=twiml, media_type="text/xml")

    # Catch-all
    return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="text/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
