import sys
import os
import json
from googleapiclient.discovery import build

sys.path.insert(0, os.path.dirname(__file__))
from config import Config
from sheets_reader import SheetsReader

reader = SheetsReader(Config.CRM_SPREADSHEET_ID, [])
reader.authenticate()
sheet_metadata = reader.service.spreadsheets().get(spreadsheetId=Config.CRM_SPREADSHEET_ID).execute()
sheets = sheet_metadata.get('sheets', '')
for sheet in sheets:
    print(sheet.get("properties", {}).get("title", ""))
