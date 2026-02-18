import os
from twilio.rest import Client
from dotenv import load_dotenv
from automation.utils import send_slack_notification

load_dotenv()

# Credentials
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def handle_missed_call(customer_phone):
    """
    Triggered by Twilio 'StatusCallback' when a call is missed/busy/no-answer.
    """
    print(f"--- Missed Call Detected from {customer_phone} ---")
    
    # 2. Send the Recovery SMS
    recovery_message = (
        "Hey! This is the team at AI Revenue Desk. So sorry we missed your call! "
        "What can we help you with today? (We're still available to book you in via text right now!)"
    )
    
    try:
        message = client.messages.create(
            body=recovery_message,
            from_=TWILIO_PHONE,
            to=customer_phone
        )
        print(f"SMS Sent: {message.sid}")
        
        # 3. Real-Time Monitoring: Slack Alert
        alert_msg = f"💥 *Missed Call Recovered!* \nCustomer: {customer_phone}\nAI has sent an automated recovery SMS."
        send_slack_notification(alert_msg)
        
        # 4. Log to Dashboard
        log_recovery_attempt(customer_phone)
        
    except Exception as e:
        print(f"Error sending SMS: {e}")

def log_recovery_attempt(phone):
    # Logic to update the performance dashboard tracker
    pass

if __name__ == "__main__":
    # Test with a dummy number
    # handle_missed_call("+1234567890")
    print("Agent ready to handle missed calls.")
