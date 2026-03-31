from dotenv import load_dotenv
from automation.utils import send_slack_notification
from automation.ghl_client import log_missed_call

load_dotenv()


def handle_missed_call(customer_phone):
    """
    Triggered by Twilio StatusCallback when a call is missed/busy/no-answer.
    Creates contact in GHL and sends recovery SMS via GHL API.
    """
    print(f"--- Missed Call from {customer_phone} ---")

    # 1. GHL: create contact + send recovery SMS
    log_missed_call(customer_phone)

    # 2. Notify team on Slack
    send_slack_notification(
        f"💥 *Missed Call*\n"
        f"📞 {customer_phone}\n"
        f"GHL contact created and recovery SMS sent."
    )


if __name__ == "__main__":
    print("Missed call handler ready.")
