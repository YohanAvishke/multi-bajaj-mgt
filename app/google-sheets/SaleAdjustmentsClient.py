from __future__ import print_function

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from datetime import date
from app.InventoryBot import inventory_adjustment
from app.config import ROOT_DIR

import csv
import json
import os.path
import pandas as pd

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '18kz-I9F90_vL60zHbGmtl8LMiAnJzy2nN_2DHzjJMIw'
RANGE_NAME = 'A:D'
MAIN_ADJUSTMENT_FILE = f'{ROOT_DIR}/data/inventory/adjustment.sales.json'
DATED_ADJUSTMENT_FILE = f"{ROOT_DIR}/data/inventory/adjustments/{date.today()}-adjustment.csv"


def get_service():
    credentials = None

    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            credentials = flow.run_local_server(port = 0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())

    return build('sheets', 'v4', credentials = credentials)


get_spreadsheet_by_data_filter_request_body = {
    'data_filters': [],
    'include_grid_data': False
    }


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
        json.dump(enriched_adjustments, file)
    print('Adjustments saved')


def create_dated_adjustment():
    with open(MAIN_ADJUSTMENT_FILE, "r") as file:
        adjustments = json.load(file)

    with open(DATED_ADJUSTMENT_FILE, "w") as adj_csv_file:
        field_names = ("name", "Product/Internal Reference", "Counted Quantity")
        adj_writer = csv.DictWriter(adj_csv_file, fieldnames = field_names, delimiter = ',', quotechar = '"',
                                    quoting = csv.QUOTE_MINIMAL)
        adj_writer.writeheader()

        for adjustment in adjustments:
            adj_ref = None
            for product in adjustment["Products"]:
                product_number = product["PartNumber"]
                product_count = product["Quantity"]
                adj_ref = f"Sales of {product['Date']}" if product['Date'] is not None else adj_ref
                adj_writer.writerow({"name": adj_ref,
                                     "Product/Internal Reference": product_number,
                                     "Counted Quantity": float(product_count)})


def main():
    service = get_service()
    raw_df = get_sheet_data(service)
    adjustments = extract_adjustments(raw_df)
    save_adjustments(adjustments)
    create_dated_adjustment()
    inventory_adjustment()


if __name__ == '__main__':
    main()
