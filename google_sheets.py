import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import os

load_dotenv()
sheet = os.getenv("SPREADSHEET_ID")

def get_sheet(sheet_number: int):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet).get_worksheet(sheet_number)

def get_all_data(sheet_number: int):
    sheet = get_sheet(sheet_number)
    return sheet.get_all_records()