# AI Revenue Desk™ — Technical Setup Guide

## 1. The Unified Engine (`app.py`)
We have consolidated all the individual scripts into a single, production-ready FastAPI application. This is the "brain" of the service that you host.

### How to Run the Whole Package:
1.  **Install dependencies:**
    ```bash
    pip install -r automation/requirements.txt
    ```
2.  **Start the Engine:**
    ```bash
    python3 automation/app.py
    ```
    *The server will start at `http://localhost:8000`.*

## 2. Webhook Connection Map
Point your external tools to these specific endpoints:

| Tool | Event | Webhook URL |
| :--- | :--- | :--- |
| **Retell AI** | Post-Call Webhook | `https://your-domain.com/webhooks/voice-sync` |
| **Twilio** | Status Callback | `https://your-domain.com/webhooks/missed-call` |
| **Twilio** | Messaging Webhook | `https://your-domain.com/webhooks/sms-agent` |

## 3. The "Sellable Package" Structure
When you deliver this to a client, you are giving them:
1.  **The Private Dashboard:** Their custom Google Sheet.
2.  **The Voice Agent:** The Retell configuration.
3.  **The Engine:** The `automation/` folder running on a server (or your agency infrastructure).
4.  **The Reporting:** The weekly ROI summaries.

## 5. Testing Order
1.  **Level 1 (Voice):** Call your Twilio number. Verify the AI answers and qualifies you.
2.  **Level 2 (Recovery):** Call and hang up before it answers. Verify you receive the recovery SMS within 10 seconds.
3.  **Level 3 (Booking):** Reply to the SMS. Verify the AI SMS agent responds and tries to book a slot.
4.  **Level 4 (CRM):** Check your CRM (or the mock log in `webhook_handler.py`) to see if the data synced.
