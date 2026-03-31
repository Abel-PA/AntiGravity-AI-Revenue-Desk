import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load client-specific SMS prompt if available, otherwise use PA Digital Growth default
_slug = os.getenv("CLIENT_SLUG")
_sms_prompt_path = os.path.join("clients", _slug, "sms_prompt.md") if _slug else None
if _sms_prompt_path and os.path.exists(_sms_prompt_path):
    with open(_sms_prompt_path) as _f:
        SYSTEM_PROMPT = _f.read()
else:
    SYSTEM_PROMPT = """
You are the AI SMS assistant for PA Digital Growth (padigitalgrowth.com), a premium digital agency.

Your job is to respond to inbound text messages from people who have either:
- Just had a call with our AI receptionist
- Missed our call and replied to our follow-up SMS
- Texted us directly to enquire about our services

Services we offer:
- Training (digital tools, AI, marketing platforms)
- AI Solutions (custom AI agents, automations, chatbots)
- SEO Work (rankings, local SEO, organic growth)
- Web Design & Development
- Social Media & Content / Paid Ads

Rules:
- Be warm, professional, and concise. SMS should be under 160 characters where possible.
- Never quote prices. Tell them a strategist will provide a custom proposal.
- If they want to speak to someone, let them know the team will be in touch as soon as possible.
- If they want to book a call, direct them to reply with their availability or preferred time.
- If it sounds like spam or a sales pitch, politely disengage.

Goal: Understand what they need, keep the conversation warm, and get them to a point where the team can follow up.
"""


def get_ai_sms_response(_customer_phone, message_body, history=None):
    """
    Generates an AI SMS response for an inbound text message.
    """
    if history is None:
        history = []

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history:
        messages.append(h)
    messages.append({"role": "user", "content": message_body})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Error: {e}")
        return "Sorry, I'm having a little trouble right now. Our team will get back to you as soon as possible — PA Digital Growth."


if __name__ == "__main__":
    test_msg = "Hi, I just had a call about AI automation for my business. Can you tell me more?"
    print(f"User: {test_msg}")
    print(f"AI: {get_ai_sms_response('+12345678901', test_msg)}")
