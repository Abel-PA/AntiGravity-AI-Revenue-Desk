from fastapi import FastAPI, Request, BackgroundTasks
from contextlib import asynccontextmanager
import os
import time
from dotenv import load_dotenv

# Import our custom modules
from automation.webhooks.webhook_handler import process_call_data
from automation.webhooks.missed_call_recovery import handle_missed_call
from automation.webhooks.sms_ai_agent import get_ai_sms_response
from automation.utils import send_slack_notification
from twilio.rest import Client

load_dotenv()

# ── Deduplication: track recently processed call_ids to prevent double-firing ──
# Stores {call_id: timestamp}. Entries older than 5 minutes are discarded.
_processed_calls: dict = {}
_DEDUP_TTL = 300  # seconds

def _already_processed(call_id: str) -> bool:
    """Returns True if this call_id was already processed within the TTL window."""
    if not call_id:
        return False
    now = time.time()
    # Evict stale entries
    stale = [k for k, t in _processed_calls.items() if now - t > _DEDUP_TTL]
    for k in stale:
        del _processed_calls[k]
    if call_id in _processed_calls:
        return True
    _processed_calls[call_id] = now
    return False


# ── Startup: validate critical env vars and alert Slack if anything is missing ──
REQUIRED_ENV_VARS = {
    "GHL_API_KEY": "GoHighLevel API — leads won't reach CRM",
    "GHL_LOCATION_ID": "GoHighLevel Location — leads won't reach CRM",
    "SLACK_WEBHOOK_URL": "Slack alerts — team won't be notified of calls",
    "TWILIO_ACCOUNT_SID": "Twilio — SMS and call routing will fail",
    "TWILIO_AUTH_TOKEN": "Twilio — SMS and call routing will fail",
    "TWILIO_PHONE_NUMBER": "Twilio — outbound SMS won't send",
    "OPENAI_API_KEY": "OpenAI — transcript fallback extraction disabled",
}

@asynccontextmanager
async def lifespan(_app: FastAPI):
    missing = [f"• `{k}` — {v}" for k, v in REQUIRED_ENV_VARS.items() if not os.getenv(k)]
    if missing:
        msg = (
            "⚠️ *AI Revenue Desk — Missing Config at Startup*\n"
            + "\n".join(missing)
            + "\nFix these in Railway environment variables."
        )
        print(msg)
        send_slack_notification(msg)
    else:
        print("✅ All required environment variables present.")
        send_slack_notification("✅ *AI Revenue Desk is online* — all systems configured and ready.")
    yield


app = FastAPI(title="AI Revenue Desk™ Engine", lifespan=lifespan)

# Twilio Client for SMS responses
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

@app.get("/")
async def root():
    return {"status": "online", "system": "AI Revenue Desk Engine v1.0"}


@app.get("/health")
async def health():
    """Lightweight health check. Returns config status for each critical service."""
    checks = {k: bool(os.getenv(k)) for k in REQUIRED_ENV_VARS}
    all_ok = all(checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
    }

@app.post("/webhooks/voice-sync")
async def retell_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives post-call data from Retell AI.
    Filter for 'call_analyzed' to prevent duplicate Slack/Sheets events.
    """
    payload = await request.json()
    event_type = payload.get("event")
    
    print(f"[Retell Webhook] Event: {event_type} | Keys: {list(payload.keys())}")

    call_obj = payload.get("call") if isinstance(payload.get("call"), dict) else payload
    call_id = call_obj.get("call_id") or payload.get("call_id")

    if event_type == "call_started":
        call = payload.get("call", {})
        caller = call.get("from_number") or call.get("customer_number") or "Unknown number"
        send_slack_notification(f"📞 *Call Started* — AI agent is speaking to {caller} right now.")

    elif event_type == "call_analyzed":
        print("[Retell] call_analyzed received — processing lead...")
        if _already_processed(call_id):
            print(f"[Retell] Duplicate call_analyzed ignored for call_id={call_id}")
        else:
            background_tasks.add_task(process_call_data, payload)

    elif event_type == "call_ended":
        # Fallback: Retell sometimes sends call_ended without a following call_analyzed
        call = payload.get("call", {})
        has_analysis = bool(call.get("analysis") or call.get("call_analysis"))
        print(f"[Retell] call_ended received — has_analysis={has_analysis}")
        if has_analysis:
            if _already_processed(call_id):
                print(f"[Retell] Duplicate call_ended ignored for call_id={call_id}")
            else:
                background_tasks.add_task(process_call_data, payload)
        else:
            print("[Retell] call_ended has no analysis — waiting for call_analyzed event")

    else:
        print(f"[Retell] Unhandled event type: {event_type}")

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
    Rings the real phone for 6 seconds.
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
  <Dial timeout="6" answerOnBridge="true" action="{action_url}" method="POST">
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
