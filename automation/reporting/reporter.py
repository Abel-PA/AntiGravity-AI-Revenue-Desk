import os
import sys
from datetime import datetime, timedelta
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class RevenueReporter:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        self.retainer_fee = 2000 # Default Tier 1 Retainer

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
            raise FileNotFoundError("Credentials.json not found.")

    def run_weekly_report(self):
        """
        Reads raw logs, aggregates data, and updates the Executive Dashboard.
        """
        print("📊 Generating Weekly Revenue Report...")
        
        # 1. Read Raw Data
        # We try AI Lead Log first, then Sheet1
        raw_data = None
        for tab in ['AI Lead Log', 'Sheet1']:
            try:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{tab}!A2:H'
                ).execute()
                raw_data = result.get('values', [])
                if raw_data:
                    print(f"✅ Found {len(raw_data)} rows in '{tab}'")
                    break
            except:
                continue

        if not raw_data:
            print("❌ No data found to report on.")
            return

        # 2. Filter & Aggregate (Last 7 Days)
        now = datetime.now()
        one_week_ago = now - timedelta(days=7)
        
        total_calls = 0
        total_booked = 0
        total_recovered = 0
        total_revenue = 0

        for row in raw_data:
            try:
                # row[0] is Timestamp: "2026-02-16 10:51:29"
                ts = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                if ts >= one_week_ago:
                    total_calls += 1
                    status = row[6].lower()
                    if "booked" in status:
                        total_booked += 1
                    if "recovered" in status:
                        total_recovered += 1
                    
                    rev = float(row[7]) if row[7] else 0
                    total_revenue += rev
            except Exception as e:
                # print(f"Skipping row: {e}")
                continue

        # 3. Calculate METRICS
        booking_rate = (total_booked / total_calls * 100) if total_calls > 0 else 0
        weekly_cost = self.retainer_fee / 4 # Rough weekly estimate
        roi = (total_revenue / weekly_cost) if weekly_cost > 0 else 0

        # 4. Prepare Dashboard Data
        # Format: Stat Name | Value | Description
        dashboard_rows = [
            ["EXECUTIVE REVENUE DASHBOARD", "", f"Report Generated: {now.strftime('%Y-%m-%d')}"],
            ["", "", ""],
            ["KEY PERFORMANCE INDICATORS (Last 7 Days)", "", ""],
            ["---------------------------------", "", ""],
            ["Total Calls Handled", total_calls, "Every inbound lead processed by AI"],
            ["Total Jobs Booked", total_booked, "Appointments added to schedule"],
            ["Missed Call Recoveries", total_recovered, "Leads saved via SMS recovery"],
            ["AI Booking Rate", f"{booking_rate:.1f}%", "Efficiency of the AI voice agent"],
            ["", "", ""],
            ["FINANCIAL IMPACT", "", ""],
            ["---------------------------------", "", ""],
            ["Est. Attributed Revenue", f"${total_revenue:,.2f}", "Gross value of AI-booked jobs"],
            ["Weekly Operating Cost", f"${weekly_cost:,.2f}", "Prorated retainer fee"],
            ["Weekly ROI Multiplier", f"{roi:.2f}x", "Return on investment this week"],
            ["", "", ""],
            ["Recommended Action", "Scale Ad Spend" if roi > 5 else "Optimize Prompt", "AI-driven growth suggestion"]
        ]

        # 5. Write to Sheet (Executive Dashboard)
        self._write_to_dashboard(dashboard_rows)

    def _write_to_dashboard(self, rows):
        tab_name = "Executive Dashboard"
        
        # Check if tab exists, if not create it
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_exists = any(s['properties']['title'] == tab_name for s in spreadsheet.get('sheets', []))
            
            if not sheet_exists:
                batch_update_request = {
                    'requests': [{'addSheet': {'properties': {'title': tab_name}}}]
                }
                self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=batch_update_request).execute()
                print(f"✨ Created new tab: {tab_name}")
        except Exception as e:
            print(f"Note on tab creation: {e}")

        # Clear and Write
        try:
            self.service.spreadsheets().values().clear(spreadsheetId=self.spreadsheet_id, range=f"{tab_name}!A1:Z100").execute()
            
            body = {'values': rows}
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{tab_name}!A1",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            print(f"✅ Dashboard updated: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}")
        except Exception as e:
            print(f"❌ Error updating dashboard: {e}")

if __name__ == "__main__":
    reporter = RevenueReporter()
    reporter.run_weekly_report()
