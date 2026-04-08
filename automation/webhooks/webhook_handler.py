import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from automation.utils import send_slack_notification
from automation.ghl_client import log_call_lead
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_from_transcript(transcript):
    """
    AI fallback extraction using GPT-4o-mini when Retell's structured data is missing.
    Tailored for PA Digital Growth's full service offering.
    """
    if not transcript:
        return {}

    print("🤖 Triggering AI Data Extraction from Transcript...")

    prompt = f"""
You are a data extraction assistant for PA Digital Growth, a digital agency.
Extract the following from this call transcript:

1. Customer Full Name
2. Email Address
3. Phone Number (if mentioned verbally — not the caller ID)
4. Company Name (if mentioned)
5. Category — MUST be exactly one of:
   AI Agents & Automation | AI Consulting | AI Training | AI Services | SEO | Web Design | Social Media | General Enquiry | Job Application | Spam/Sales
6. Budget — any budget figure or range mentioned (e.g. "around £2k a month", "£500"). Use "Not disclosed" if not mentioned.
7. Is Spam/Sales Call? (Boolean: True if job seeker, solicitor, robocall, or trying to sell something. False if genuine lead.)
8. Qualification Notes & Summary — what do they need, how urgent, any key context
9. Requested Action — one of: capture_lead | notify_sales_hot_lead | book_strategy_call | request_human_takeover | flag_spam_call
10. SMS Consent — did the caller verbally agree to receive a follow-up text message? (Boolean: True if they said yes/agreed, False if they declined or it was never asked.)

Transcript:
\"\"\"{transcript}\"\"\"

Return ONLY a JSON object with keys:
"name", "email", "phone", "company", "category", "budget", "is_spam", "notes", "action_triggered", "sms_consent"
If a field is missing or not mentioned, use null.
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return JSON only. No markdown, no explanation."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ AI Fallback Error: {e}")
        return {}


def process_call_data(call_payload):
    """
    Processes post-call data from Retell AI.
    Extracts enriched lead data and routes it to GoHighLevel (GHL) and Slack.
    """
    try:
        _process_call_data_inner(call_payload)
    except Exception as e:
        call_id = None
        try:
            call_obj = call_payload.get("call") if isinstance(call_payload.get("call"), dict) else call_payload
            call_id = call_obj.get("call_id") or call_payload.get("call_id")
        except Exception:
            pass
        print(f"❌ Fatal error in process_call_data (call_id={call_id}): {e}")
        from automation.utils import send_slack_notification
        send_slack_notification(
            f"🔴 *Webhook Processing Failed*\n"
            f"Call ID: `{call_id or 'unknown'}`\n"
            f"Error: `{type(e).__name__}: {e}`\n"
            f"Action required: Check Railway logs and manually review this call in Retell."
        )


def _process_call_data_inner(call_payload):
    call_obj = call_payload.get("call") if isinstance(call_payload.get("call"), dict) else call_payload
    call_id = call_obj.get("call_id") or call_payload.get("call_id")
    transcript = call_obj.get("transcript") or call_payload.get("transcript")
    start_timestamp = call_obj.get("start_timestamp") or int(datetime.now(timezone.utc).timestamp() * 1000)
    end_timestamp = call_obj.get("end_timestamp") or start_timestamp

    # Call time — human readable
    try:
        call_time_iso = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc).strftime('%d %b %Y, %I:%M %p UTC')
    except Exception:
        call_time_iso = str(start_timestamp)

    # Call duration in seconds
    try:
        call_duration_seconds = max(0, int((end_timestamp - start_timestamp) / 1000))
    except Exception:
        call_duration_seconds = 0

    print(f"--- Processing Call: {call_id} at {call_time_iso} ({call_duration_seconds}s) ---")

    # Extract from Retell's native structured data
    analysis = call_obj.get("analysis") or call_obj.get("call_analysis") or call_payload.get("analysis") or {}
    custom_vars = call_obj.get("custom_variables") or call_payload.get("custom_variables") or {}
    analysis.update(custom_vars)

    customer_number = call_obj.get("from_number") or call_obj.get("customer_number") or call_payload.get("from_number", "")

    customer_name = analysis.get("customer_name") or analysis.get("name") or analysis.get("contact_name")
    email = analysis.get("email")
    company = analysis.get("company") or analysis.get("company_name")
    category = analysis.get("category")
    budget = analysis.get("budget") or analysis.get("budget_signal")
    action_triggered = analysis.get("action_triggered") or "none"
    notes = (
        analysis.get("notes")
        or analysis.get("summary")
        or analysis.get("urgency_reason")
        or analysis.get("reason_for_takeover")
        or ""
    )
    is_spam = analysis.get("is_spam", False)
    sms_consent = analysis.get("sms_consent")

    # AI fallback extraction if Retell didn't capture everything
    fallback = extract_from_transcript(transcript)
    if fallback:
        customer_name = customer_name or fallback.get("name") or "Unknown"
        email = email or fallback.get("email") or ""
        company = company or fallback.get("company") or ""
        if not customer_number:
            customer_number = fallback.get("phone") or ""
        category = category or fallback.get("category") or "General Enquiry"
        budget = budget or fallback.get("budget") or "Not disclosed"
        is_spam = fallback.get("is_spam", is_spam)
        if sms_consent is None:
            sms_consent = fallback.get("sms_consent")
        if action_triggered == "none":
            action_triggered = fallback.get("action_triggered") or "capture_lead"
        if not notes:
            notes = fallback.get("notes", "No notes available.")

    # Treat None/missing consent as False — never send SMS without explicit agreement
    sms_consent = sms_consent is True

    # Determine urgency level
    if action_triggered in ["notify_sales_hot_lead", "request_human_takeover"]:
        urgency_level = "high"
    elif action_triggered == "flag_spam_call" or is_spam:
        urgency_level = "spam"
    else:
        urgency_level = "standard"

    # Package full lead data for GHL
    lead_data = {
        "call_id": call_id,
        "call_time": call_time_iso,
        "call_duration_seconds": call_duration_seconds,
        "name": customer_name or "Unknown",
        "phone": customer_number,
        "email": email or "",
        "company": company or "",
        "category": category or "General Enquiry",
        "service_interest": category or "General Enquiry",
        "budget": budget or "Not disclosed",
        "is_spam": is_spam,
        "action": action_triggered,
        "urgency": urgency_level,
        "sms_consent": sms_consent,
        "notes": notes,
        "source": "PA Digital Growth AI Agent",
        "tags": ["AI-Captured", category] if category else ["AI-Captured"]
    }

    # Spam — light alert only, skip CRM
    if urgency_level == "spam" or is_spam:
        print("⚠️ Call flagged as SPAM/Sales. Skipping CRM. Sending light Slack alert.")
        send_slack_notification(
            f"🚫 *Spam Call Filtered*\n"
            f"📞 {customer_number}  |  Reason: {notes or action_triggered}"
        )
        return

    # 1. Send to GoHighLevel (direct API — create/update contact, note, SMS, pipeline)
    print("🚀 Pushing lead to GHL via API...")
    log_call_lead(lead_data)

    # 2. Send rich Slack lead card to the team
    try:
        if urgency_level == "high":
            header = "🔥 *URGENT Lead — PA Digital Growth*"
            action_line = f"⚡ *Action Required:* URGENT — Call back as soon as possible"
        else:
            header = "✅ *New Lead — PA Digital Growth*"
            action_line = f"📋 *Action:* {action_triggered.replace('_', ' ').title()}"

        budget_display = budget if budget and budget != "Not disclosed" else "_Not disclosed_"
        company_display = company if company else "_Not provided_"
        email_display = email if email else "_Not provided_"
        consent_display = "✅ Consented" if sms_consent else "❌ Declined / Not captured"

        slack_msg = (
            f"{header}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *Name:* {lead_data['name']}\n"
            f"📞 *Phone:* {customer_number}\n"
            f"📧 *Email:* {email_display}\n"
            f"🏢 *Company:* {company_display}\n"
            f"🎯 *Interest:* {lead_data['category']}\n"
            f"⏱️ *Called:* {call_time_iso}  ({call_duration_seconds}s)\n"
            f"💰 *Budget:* {budget_display}\n"
            f"📱 *SMS Consent:* {consent_display}\n"
            f"💬 *Notes:* {notes}\n"
            f"{action_line}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        send_slack_notification(slack_msg)
    except Exception as e:
        print(f"❌ Error sending Slack Alert: {e}")


if __name__ == "__main__":
    process_call_data({
        "call": {
            "call_id": "test_ghl_001",
            "from_number": "+15550293847",
            "start_timestamp": 1743400000000,
            "end_timestamp": 1743400180000,
            "transcript": (
                "Hi, my name is James Walker, I run a marketing agency called Apex Media. "
                "We're looking at getting some AI automation built for our client intake process. "
                "My email is james@apexmedia.com. Budget is probably around two to three grand a month. "
                "Would love to speak to someone this week if possible."
            ),
        }
    })
