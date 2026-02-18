import os
import json
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def check_sheets():
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
    cred_file = 'Credentials.json' if os.path.exists('Credentials.json') else 'credentials.json'
    
    with open(cred_file, 'r') as f:
        cred_data = json.load(f)
    
    if cred_data.get('type') == 'service_account':
        creds = service_account.Credentials.from_service_account_file(cred_file, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    else:
        creds = UserCredentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/spreadsheets.readonly'])
        
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    
    print("Found sheets:")
    for sheet in sheets:
        print(f"- '{sheet['properties']['title']}'")

if __name__ == "__main__":
    check_sheets()
