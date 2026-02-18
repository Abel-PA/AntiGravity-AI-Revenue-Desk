# AI Revenue Desk™ — SMS Pipeline Logic

## 1. Missed Call Recovery (The "Speed to Lead" Engine)
**Trigger:** Inbound call to Twilio not answered or disconnected under 30 seconds without a "Booked" signal.

### Template: Initial Recovery
> "Hey, this is the team at [Company Name]. So sorry we missed your call! What can we help you with today? (We're still available to book you in via text right now if that's easier!)"

## 2. Qualification Script (The AI Logic)
**Goal:** Extract Issue, Address, and Urgency.

*   **User Info Extraction:**
    *   `{{issue}}`: "My AC is blowing hot air."
    *   `{{address}}`: "I'm at 123 Maple St."
*   **AI Logic:** If `{{address}}` is missing, ask: *"Got it. We can definitely help with that {{issue}}. What's the service address so I can check our tech's schedule for your neighborhood?"*

## 3. Booking Push
**Trigger:** Address and Issue confirmed.

> "Perfect. We have a technician in [Neighborhood] tomorrow between 8am and 10am. Does that work for you, or would the afternoon be better?"

## 4. Objection Handling Logic

| Objection | AI Response Strategy |
| :--- | :--- |
| **Price** | "I understand! Our diagnostic fee is just $79, which we waive if you move forward with the repair. Would you like to keep that slot?" |
| **"Is this a bot?"** | "I'm the AI assistant for [Company Name]! I'm here to get you booked faster because our phone lines are slammed. Should I grab that 2pm slot for you?" |
| **Privacy** | "We only use your address to send our technician. You can view our privacy policy here: [Link]." |

## 5. Re-engagement Logic (The "Ghost" Fix)
**Trigger:** No response to Booking Push after 15 minutes.

> "Still there, {{First_Name}}? That 8am-10am slot is filling up fast—should I put your name on it for now?"

## 6. Dead Lead Tagging Logic
**Trigger:** 
*   No response for 48 hours.
*   Keyword: "Wrong number", "Stop", "Don't text me".
*   Out of service area (Logic check on Zip Code).

**Action:** Update CRM status to `Closed - Lost` or `Out of Area`. Tag as `AI_DEAD_LEAD`.

---

## Decision Tree Logic (Pseudocode)

```python
def handle_sms_inbound(message, lead_state):
    if lead_state == "NEW":
        return send_qualification_question()
    elif lead_state == "QUALIFIED":
        return offer_available_slots()
    elif lead_state == "WAITING_CONFIRMATION":
        if "yes" in message.lower():
            confirm_booking()
            return "You're all set! Tech {{Tech_Name}} will see you at {{Time}}."
        else:
            return "No problem, what time works better for you?"
```

## Escalation Flags
*   **Flag 1:** Profanity detected -> Route to human supervisor.
*   **Flag 2:** Request for "Owner" or "Manager" -> Notify owner via Slack/Email.
*   **Flag 3:** Picture of a complex part sent -> Trigger "MMS Received" alert to Dispatch.
