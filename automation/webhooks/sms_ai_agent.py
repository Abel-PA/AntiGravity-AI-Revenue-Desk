import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are the AI SMS Assistant for the AI Revenue Desk (Home Services).
Your goal is to qualify lead and book appointments. 
Be concise. SMS should be under 160 characters if possible.

STEPS:
1. Identify the issue (HVAC, Plumbing, etc.)
2. Get the address.
3. Check urgency.
4. Offer a slot (Simulated: "Tomorrow morning" or "Afternoon").
5. Book the job.

Pricing: Standard diagnostic fee is $99.
Tone: Helpful, professional.
"""

def get_ai_sms_response(customer_phone, message_body, history=[]):
    """
    Generates an AI response for an inbound SMS.
    """
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
        ai_message = response.choices[0].message.content
        return ai_message
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm so sorry, I'm having a bit of trouble on my end. Can I have a service manager call you back instead?"

if __name__ == "__main__":
    # Test
    test_msg = "My AC is broken and it's 90 degrees in here."
    print(f"User: {test_msg}")
    print(f"AI: {get_ai_sms_response('+12345678', test_msg)}")
