import os
import requests
from dotenv import load_dotenv

load_dotenv()

def validate_address(address_string):
    """
    Uses Google Maps Geocoding API to validate and format an address.
    Returns (formatted_address, is_valid, place_id)
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("⚠️ GOOGLE_MAPS_API_KEY not set. Skipping validation.")
        return address_string, True, None

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address_string}&key={api_key}"
    
    try:
        response = requests.get(url).json()
        if response["status"] == "OK":
            result = response["results"][0]
            # Check if it's a precise address (not just a city or state)
            location_type = result["geometry"]["location_type"]
            is_precise = location_type in ["ROOFTOP", "RANGE_INTERPOLATED"]
            
            return result["formatted_address"], is_precise, result["place_id"]
        else:
            return address_string, False, None
    except Exception as e:
        print(f"❌ Geocoding Error: {e}")
        return address_string, False, None

def send_slack_notification(message):
    """
    Sends a message to a Slack channel via Webhook.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ SLACK_WEBHOOK_URL not set. Skipping notification.")
        return

    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("✅ Slack notification sent successfully!")
        else:
            print(f"❌ Slack Error: Received status code {response.status_code}. Response: {response.text}")
    except Exception as e:
        print(f"❌ Slack Connection Error: {e}")

if __name__ == "__main__":
    # Test Address
    addr, valid, pid = validate_address("1600 Amphitheatre Pkwy, Mountain View, CA")
    print(f"Validated: {addr} (Valid: {valid})")
    
    # Test Slack
    print("Testing Slack Webhook...")
    send_slack_notification("🚀 *AI Revenue Desk:* Connection Test Successful!")
