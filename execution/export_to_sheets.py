#!/usr/bin/env python3
"""
Google Sheets Export Engine
Consolidates lead data from multiple files and writes to a Google Sheet.
Handles category combinations (e.g. HVAC + Plumbing).
"""

import os
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials as UserCredentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from dotenv import load_dotenv
    import json
except ImportError:
    print("ERROR: Google API libraries or python-dotenv not installed.")
    print("Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class SheetsExporter:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.leads_db = {}
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')

    def _authenticate(self):
        # Check for Credentials.json (uppercase) or credentials.json (lowercase)
        cred_file = 'Credentials.json' if os.path.exists('Credentials.json') else 'credentials.json'
        
        if not os.path.exists(cred_file):
            # Try to see if we have an existing token for user auth
            if os.path.exists('token.json'):
                return UserCredentials.from_authorized_user_file('token.json', SCOPES)
            print(f"\n❌ ERROR: '{cred_file}' not found in root directory.")
            sys.exit(1)

        # Detect credential type
        with open(cred_file, 'r') as f:
            cred_data = json.load(f)
        
        if cred_data.get('type') == 'service_account':
            print("🔐 Using Service Account credentials...")
            return service_account.Credentials.from_service_account_file(cred_file, scopes=SCOPES)
        else:
            print("👤 Using OAuth 2.0 (User) credentials...")
            creds = None
            if os.path.exists('token.json'):
                creds = UserCredentials.from_authorized_user_file('token.json', SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            return creds

    def parse_enriched_file(self, filepath):
        """Parse enriched lead files and merge into leads_db."""
        print(f"📖 Parsing {filepath}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract source category from filename
        category_hint = ""
        if 'hvac' in filepath.lower(): category_hint = "HVAC"
        elif 'roofing' in filepath.lower() or 'roofer' in filepath.lower(): category_hint = "Roofing"
        elif 'plumber' in filepath.lower() or 'plumbing' in filepath.lower(): category_hint = "Plumbing"

        lead_sections = re.split(r'LEAD #\d+ - SCORE: \d+/5 ⭐\n-+', content)
        for section in lead_sections[1:]:
            # Simple extraction
            name = self._get_field(section, r'Business Name:\s+(.+)')
            if not name: continue

            website = self._get_field(section, r'Website:\s+(.+)')
            phone = self._get_field(section, r'Phone:\s+(.+)')
            email = self._get_field(section, r'Email:\s+(.+)')
            score = self._get_field(section, r'SCORE:\s+(\d+)') # Note: regex might need adjustment based on section break
            # Actually, score is in the header we split by. Let's re-extract from the start of section if possible
            # or just grep it. 
            score_match = re.search(r'(\d+)/5 ⭐', section) # In case it's inside
            score = score_match.group(1) if score_match else "1"

            # Socials
            fb = self._get_field(section, r'Facebook:\s+(.+)')
            ig = self._get_field(section, r'Instagram:\s+(.+)')
            tk = self._get_field(section, r'TikTok:\s+(.+)')
            li = self._get_field(section, r'LinkedIn:\s+(.+)')
            x = self._get_field(section, r'Twitter/X:\s+(.+)')

            # Standardize "Not found"
            def clean(val): return val if val and "Not found" not in val else ""

            # Use Website + Name as unique key
            key = f"{name.lower().strip()}|{clean(website).lower()}"
            
            if key not in self.leads_db:
                self.leads_db[key] = {
                    'Name': name.strip(),
                    'Categories': {category_hint} if category_hint else set(),
                    'Score': int(score),
                    'Website': clean(website),
                    'Phone': clean(phone),
                    'Email': clean(email),
                    'Facebook': clean(fb),
                    'Instagram': clean(ig),
                    'TikTok': clean(tk),
                    'LinkedIn': clean(li),
                    'X': clean(x)
                }
            else:
                # Merge
                if category_hint: self.leads_db[key]['Categories'].add(category_hint)
                self.leads_db[key]['Score'] = max(self.leads_db[key]['Score'], int(score))
                if not self.leads_db[key]['Email'] and clean(email):
                    self.leads_db[key]['Email'] = clean(email)
                if not self.leads_db[key]['Website'] and clean(website):
                    self.leads_db[key]['Website'] = clean(website)

    def _get_field(self, text, pattern):
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    def create_and_write(self, title):
        try:
            if self.spreadsheet_id:
                sheet_id = self.spreadsheet_id
                print(f"📂 Using existing Spreadsheet ID: {sheet_id}")
            else:
                # Create a new Spreadsheet
                spreadsheet = {
                    'properties': {'title': title}
                }
                spreadsheet = self.service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
                sheet_id = spreadsheet.get('spreadsheetId')
                print(f"✅ Created new Spreadsheet: https://docs.google.com/spreadsheets/d/{sheet_id}")

            # Prepare Data
            headers = ["Name", "Category", "Score", "Website", "Phone", "Email", "Facebook", "Instagram", "TikTok", "LinkedIn", "X"]
            rows = [headers]
            
            # Sort by Score descending
            sorted_leads = sorted(self.leads_db.values(), key=lambda x: x['Score'], reverse=True)
            
            for lead in sorted_leads:
                # Combine categories
                cats = sorted(list(lead['Categories']))
                cat_label = ", ".join(cats) if cats else "Service Business"
                
                rows.append([
                    lead['Name'],
                    cat_label,
                    lead['Score'],
                    lead['Website'],
                    lead['Phone'],
                    lead['Email'],
                    lead['Facebook'],
                    lead['Instagram'],
                    lead['TikTok'],
                    lead['LinkedIn'],
                    lead['X']
                ])

            # Write Rows
            body = {'values': rows}
            # We use 'values().update' which overwrites range. 
            # We target Sheet1!A1. If the sheet has a different name, this might fail or create new.
            self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id, range="Sheet1!A1",
                valueInputOption="USER_ENTERED", body=body).execute()

            # Format Header (Bold + Freeze)
            # Note: sheetId 0 is usually the first sheet 'Sheet1'
            requests = [
                {
                    'repeatCell': {
                        'range': {'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 1},
                        'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
                        'fields': 'userEnteredFormat(textFormat)'
                    }
                },
                {
                    'updateSheetProperties': {
                        'properties': {'sheetId': 0, 'gridProperties': {'frozenRowCount': 1}},
                        'fields': 'gridProperties.frozenRowCount'
                    }
                }
            ]
            
            # Try to format, but don't fail if sheetId 0 doesn't exist (though it usually does)
            try:
                self.service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={'requests': requests}).execute()
            except:
                pass

            print(f"📊 Exported {len(rows)-1} consolidated leads.")
            return sheet_id

        except HttpError as err:
            print(f"❌ API Error: {err}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Export enriched leads to Google Sheets.')
    parser.add_argument('files', nargs='+', help='Enriched lead text files to parse')
    parser.add_argument('--title', default=f"Leads Export {datetime.now().strftime('%Y-%m-%d')}", help='Spreadsheet title')
    
    args = parser.parse_args()
    
    exporter = SheetsExporter()
    for f in args.files:
        if os.path.exists(f):
            exporter.parse_enriched_file(f)
        else:
            print(f"⚠️ Warning: File {f} not found.")

    if not exporter.leads_db:
        print("❌ No leads found to export.")
        sys.exit(1)

    exporter.create_and_write(args.title)

if __name__ == "__main__":
    main()
