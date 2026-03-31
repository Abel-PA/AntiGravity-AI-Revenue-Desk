"""
GoHighLevel API Client — PA Digital Growth
Direct REST API integration (no webhook workflows needed).

Handles: contact create/update, notes, SMS, pipeline opportunities.
Docs: https://highlevel.stoplight.io/docs/integrations
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
GHL_PIPELINE_ID = os.getenv("GHL_PIPELINE_ID")                         # Optional
GHL_STAGE_NEW_LEAD = os.getenv("GHL_PIPELINE_STAGE_NEW_LEAD")          # Optional
GHL_STAGE_HOT_LEAD = os.getenv("GHL_PIPELINE_STAGE_HOT_LEAD")          # Optional

BASE_URL = "https://services.leadconnectorhq.com"

HEADERS = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Version": "2021-07-28",
    "Content-Type": "application/json",
}


def _is_configured():
    if not GHL_API_KEY or not GHL_LOCATION_ID:
        print("⚠️  GHL_API_KEY or GHL_LOCATION_ID not set — skipping GHL operation.")
        return False
    return True


# ─────────────────────────────────────────────
# Contact Management
# ─────────────────────────────────────────────

def find_contact_by_phone(phone: str) -> Optional[str]:
    """Returns the contactId if a contact with this phone already exists, else None."""
    if not _is_configured() or not phone:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/contacts/",
            headers=HEADERS,
            params={"locationId": GHL_LOCATION_ID, "query": phone},
            timeout=10,
        )
        if resp.status_code == 200:
            contacts = resp.json().get("contacts", [])
            if contacts:
                return contacts[0].get("id")
    except Exception as e:
        print(f"❌ GHL find_contact error: {e}")
    return None


def upsert_contact(lead_data: dict) -> Optional[str]:
    """
    Creates a new contact or updates an existing one (matched by phone).
    Returns the contactId or None on failure.
    """
    if not _is_configured():
        return None

    phone = lead_data.get("phone", "")
    existing_id = find_contact_by_phone(phone)

    # Split name into first/last best-effort
    full_name = lead_data.get("name", "").strip()
    parts = full_name.split(" ", 1)
    first_name = parts[0] if parts else "Unknown"
    last_name = parts[1] if len(parts) > 1 else ""

    # Build tags list
    tags = ["AI-Captured"]
    if lead_data.get("category"):
        tags.append(lead_data["category"])
    if lead_data.get("urgency") == "high":
        tags.append("Hot Lead")

    payload = {
        "locationId": GHL_LOCATION_ID,
        "firstName": first_name,
        "lastName": last_name,
        "phone": phone,
        "email": lead_data.get("email") or "",
        "companyName": lead_data.get("company") or "",
        "source": lead_data.get("source", "PA Digital Growth AI Agent"),
        "tags": tags,
    }

    try:
        if existing_id:
            resp = requests.put(
                f"{BASE_URL}/contacts/{existing_id}",
                headers=HEADERS,
                json=payload,
                timeout=10,
            )
            action = "Updated"
        else:
            resp = requests.post(
                f"{BASE_URL}/contacts/",
                headers=HEADERS,
                json=payload,
                timeout=10,
            )
            action = "Created"

        if resp.status_code in [200, 201]:
            contact_id = resp.json().get("contact", {}).get("id") or existing_id
            print(f"✅ GHL Contact {action}: {contact_id}")
            return contact_id
        else:
            print(f"⚠️  GHL upsert_contact {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"❌ GHL upsert_contact error: {e}")
    return None


def add_note(contact_id: str, note_body: str):
    """Attaches a note (call summary) to a GHL contact."""
    if not _is_configured() or not contact_id:
        return
    try:
        resp = requests.post(
            f"{BASE_URL}/contacts/{contact_id}/notes",
            headers=HEADERS,
            json={"body": note_body},
            timeout=10,
        )
        if resp.status_code in [200, 201]:
            print("✅ GHL Note added.")
        else:
            print(f"⚠️  GHL add_note {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"❌ GHL add_note error: {e}")


# ─────────────────────────────────────────────
# SMS
# ─────────────────────────────────────────────

def send_sms(contact_id: str, message: str):
    """Sends an SMS to a contact via GHL Conversations API."""
    if not _is_configured() or not contact_id:
        return
    try:
        resp = requests.post(
            f"{BASE_URL}/conversations/messages",
            headers=HEADERS,
            json={
                "type": "SMS",
                "contactId": contact_id,
                "locationId": GHL_LOCATION_ID,
                "message": message,
            },
            timeout=10,
        )
        if resp.status_code in [200, 201]:
            print("✅ GHL SMS sent.")
        else:
            print(f"⚠️  GHL send_sms {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"❌ GHL send_sms error: {e}")


# ─────────────────────────────────────────────
# Pipeline / Opportunities
# ─────────────────────────────────────────────

def add_to_pipeline(contact_id: str, lead_name: str, category: str, urgency: str):
    """
    Creates a pipeline opportunity for this contact.
    Requires GHL_PIPELINE_ID in .env. Stage is chosen by urgency level.
    Skipped silently if pipeline is not configured.
    """
    if not _is_configured() or not contact_id or not GHL_PIPELINE_ID:
        return

    stage_id = GHL_STAGE_HOT_LEAD if urgency == "high" else GHL_STAGE_NEW_LEAD

    payload = {
        "pipelineId": GHL_PIPELINE_ID,
        "locationId": GHL_LOCATION_ID,
        "name": f"{lead_name} — {category}",
        "contactId": contact_id,
        "status": "open",
    }
    if stage_id:
        payload["pipelineStageId"] = stage_id

    try:
        resp = requests.post(
            f"{BASE_URL}/opportunities/",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        if resp.status_code in [200, 201]:
            print("✅ GHL Opportunity created.")
        else:
            print(f"⚠️  GHL add_to_pipeline {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"❌ GHL add_to_pipeline error: {e}")


# ─────────────────────────────────────────────
# High-level helpers used by webhook_handler
# ─────────────────────────────────────────────

def log_call_lead(lead_data: dict):
    """
    Full post-call flow:
    1. Create/update contact
    2. Attach call note
    3. Send SMS confirmation
    4. Add to pipeline (if configured)
    """
    contact_id = upsert_contact(lead_data)
    if not contact_id:
        return

    # Build note body
    note = (
        f"📞 AI Agent Call — {lead_data.get('call_time', '')}\n"
        f"Duration: {lead_data.get('call_duration_seconds', 0)}s\n"
        f"Interest: {lead_data.get('category', '')}\n"
        f"Budget: {lead_data.get('budget', 'Not disclosed')}\n"
        f"Action: {lead_data.get('action', '')}\n"
        f"Urgency: {lead_data.get('urgency', '')}\n\n"
        f"Notes: {lead_data.get('notes', '')}"
    )
    add_note(contact_id, note)

    # SMS confirmation
    name = lead_data.get("name", "there")
    sms_msg = (
        f"Hi {name.split()[0]}, thanks for calling PA Digital Growth! "
        f"Someone from our team will be in touch with you as soon as possible. "
        f"In the meantime, feel free to reply to this message with any questions."
    )
    send_sms(contact_id, sms_msg)

    # Pipeline
    add_to_pipeline(
        contact_id,
        lead_data.get("name", "Unknown"),
        lead_data.get("category", "General Enquiry"),
        lead_data.get("urgency", "standard"),
    )


def log_missed_call(phone: str):
    """
    Missed call flow:
    1. Create contact (phone only)
    2. Tag as missed call
    3. Send recovery SMS
    """
    if not _is_configured() or not phone:
        return

    # Create minimal contact
    existing_id = find_contact_by_phone(phone)
    if existing_id:
        contact_id = existing_id
        print(f"ℹ️  Existing contact found for missed call: {contact_id}")
    else:
        try:
            resp = requests.post(
                f"{BASE_URL}/contacts/",
                headers=HEADERS,
                json={
                    "locationId": GHL_LOCATION_ID,
                    "phone": phone,
                    "source": "Missed Call - PA Digital Growth",
                    "tags": ["Missed Call", "AI-Recovery"],
                },
                timeout=10,
            )
            if resp.status_code in [200, 201]:
                contact_id = resp.json().get("contact", {}).get("id")
                print(f"✅ GHL Contact created for missed call: {contact_id}")
            else:
                print(f"⚠️  GHL missed call contact {resp.status_code}: {resp.text}")
                return
        except Exception as e:
            print(f"❌ GHL log_missed_call error: {e}")
            return

    client_name = os.getenv("CLIENT_NAME", "PA Digital Growth")
    sms_msg = (
        f"Hey! Sorry we missed your call — this is the team at {client_name}. "
        f"What can we help you with today? Reply here and we'll get straight back to you."
    )
    send_sms(contact_id, sms_msg)
