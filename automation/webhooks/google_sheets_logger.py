import os
import sys
from datetime import datetime
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class RevenueDeskLogger:
    def __init__(self):
        self.creds = self._authenticate()
        # discovery_service_local=True avoids the background network call that causes SegFaults in some environments
        self.service = build('sheets', 'v4', credentials=self.creds, static_discovery=True)
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')

    def _authenticate(self):
        # 1. Try Environment Variable (For Railway/Cloud)
        env_creds = os.getenv("GOOGLE_CREDS_JSON")
        if env_creds:
            print("🔐 Using credentials from GOOGLE_CREDS_JSON environment variable...")
            cred_data = json.loads(env_creds)
            return service_account.Credentials.from_service_account_info(cred_data, scopes=SCOPES)

        # 2. Fallback to Local Files
        cred_file = 'Credentials.json' if os.path.exists('Credentials.json') else 'credentials.json'
        if not os.path.exists(cred_file):
            if os.path.exists('token.json'):
                return UserCredentials.from_authorized_user_file('token.json', SCOPES)
            raise FileNotFoundError("Credentials.json or token.json not found. Please authenticate.")

    def log_call(self, data):
        """
        Appends a row to the 'AI Lead Log' sheet (falls back to Sheet1).
        Data keys: [Call ID, Name, Phone, Address, Issue, Status, Est Revenue]
        """
        if not self.spreadsheet_id:
            print("❌ GOOGLE_SHEETS_ID not set in .env")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row = [
            timestamp,
            data.get('call_id', ''),
            data.get('name', 'Unknown'),
            data.get('phone', ''),
            data.get('address', ''),
            data.get('issue', ''),
            data.get('status', 'Pending'),
            data.get('est_revenue', 0)
        ]

        # Try 'AI Lead Log' first, fallback to 'Sheet1'
        possible_ranges = ['AI Lead Log!A2', 'Sheet1!A2']
        
        for range_name in possible_ranges:
            try:
                body = {'values': [row]}
                result = self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
                print(f"✅ Logged to Sheets ({range_name.split('!')[0]}): {result.get('updates').get('updatedRange')}")
                return
            except Exception as e:
                if "Unable to parse range" in str(e) and range_name != possible_ranges[-1]:
                    continue # Try next range
                print(f"❌ Error logging to Sheets: {e}")

if __name__ == "__main__":
    # Test
    logger = RevenueDeskLogger()
    test_data = {
        "call_id": "TEST_123",
        "name": "Jane Doe",
        "phone": "+15550001",
        "address": "789 Pine St",
        "issue": "Broken Heater",
        "status": "Booked",
        "est_revenue": 150
    }
    logger.log_call(test_data)
