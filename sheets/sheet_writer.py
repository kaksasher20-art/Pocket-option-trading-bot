"""
Google Sheets writer — appends signal rows to a shared spreadsheet.
Auth via GCP_SERVICE_ACCOUNT_JSON env var (recommended) or credentials.json fallback.
"""

import os
import json

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_client():
    json_blob = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
    if json_blob:
        info = json.loads(json_blob)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds)


def write_signal_row(sheet_id: str, row: list):
    """Append a single row to Sheet1 of the target spreadsheet."""
    try:
        client = _get_client()
        sh = client.open_by_key(sheet_id)
        ws = sh.sheet1
        ws.append_row(row, value_input_option="USER_ENTERED")
        print(f"[SHEET] Row written: {row[1]} {row[2]} {row[4]}")
    except Exception as e:
        print(f"[SHEET ERROR] {e}")
