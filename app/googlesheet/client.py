from __future__ import print_function

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from datetime import date
from app.config import ROOT_DIR

import json
import os.path
import pandas as pd

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '18kz-I9F90_vL60zHbGmtl8LMiAnJzy2nN_2DHzjJMIw'
RANGE_NAME = 'A:D'
TOKEN_FILE = F'{ROOT_DIR}/app/googlesheet/token.json'
CREDENTIAL_FILE = f'{ROOT_DIR}/app/googlesheet/credentials.json'
MAIN_ADJUSTMENT_FILE = f'{ROOT_DIR}/data/inventory/adjustment.sales.json'
DATED_ADJUSTMENT_FILE = f"{ROOT_DIR}/data/inventory/adjustments/{date.today()}-adjustment.csv"


def get_service():
    credentials = None

    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIAL_FILE, SCOPES)
            credentials = flow.run_local_server(port = 0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())

    return build('sheets', 'v4', credentials = credentials)


def get_sheet_data(service):
    sheet = service.spreadsheets()
    request = sheet.values().get(spreadsheetId = SPREADSHEET_ID, range = RANGE_NAME)
    response = request.execute()
    values = response.get('values', [])

    if not values:
        print('No data found in the sheet')
    else:
        return pd.DataFrame(columns = ['PartNumber', 'Quantity', 'Date', 'isUploaded'], data = values)


def extract_adjustments(raw_df):
    header_indexes = raw_df.query('isUploaded == "False"').index.values.tolist()
    boundaries = header_indexes + [len(raw_df.index)]
    adjustments = [(raw_df.iloc[(boundaries[n] + 1):boundaries[n + 1]]) for n in range(len(boundaries) - 1)]
    enriched_adjustments = [adjustments[n]
                                .apply(lambda x: x.str.strip())  # Remove all whitespaces
                                .drop(columns = ['isUploaded'])  # Drop columns = ['isUploaded']
                                .to_dict('records')  # Convert dataframes into dicts
                            for n in range(len(adjustments))]

    return enriched_adjustments


def save_adjustments(adjustments):
    enriched_adjustments = []
    for adjustment in adjustments:
        enriched_adjustments.append({'Products': adjustment})

    with open(MAIN_ADJUSTMENT_FILE, 'w') as file:
        json.dump({'Adjustments': enriched_adjustments}, file)


def create_dated_adjustment():
    adjustments = pd.read_json(MAIN_ADJUSTMENT_FILE, orient = 'records').Adjustments.to_list()
    products_df = pd.json_normalize(adjustments, 'Products')

    products_df.Date = products_df.Date.fillna(method = "ffill")
    values = products_df.apply(lambda row: f'Sales of {row["Date"]}', axis = 1)
    products_df.insert(loc = 0, column = 'AdjustmentName', value = values)
    products_df = products_df.drop('Date', axis = 1)

    products_df.to_csv(DATED_ADJUSTMENT_FILE, header = ['name', 'Product/Internal Reference', 'Counted Quantity'],
                       index = False)


def main():
    service = get_service()
    raw_df = get_sheet_data(service)
    adjustments = extract_adjustments(raw_df)
    save_adjustments(adjustments)
    create_dated_adjustment()


if __name__ == '__main__':
    main()
