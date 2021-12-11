from __future__ import print_function
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import json
import os.path
import pandas as pd

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '18kz-I9F90_vL60zHbGmtl8LMiAnJzy2nN_2DHzjJMIw'
RANGE_NAME = 'A:D'
ADJUSTMENT_FILE = '../../data/inventory/adjustment.sales.json'


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
    header_indexes = raw_df.query('PartNumber == "STR_PART_NO" & isUploaded == "False"').index.values.tolist()
    boundaries = header_indexes + [len(raw_df.index)]
    # Split raw dataframe by the list of boundaries. Drop columns = ['isUploaded'] and convert sub dataframes into dicts
    adjustments = [
        (raw_df.iloc[(boundaries[n] + 1):boundaries[n + 1]]).drop(columns = ['isUploaded']).to_dict('records') for n in
        range(len(boundaries) - 1)]
    return adjustments


def save_adjustments(adjustments):
    enriched_adjustments = []
    for adjustment in adjustments:
        enriched_adjustments.append({'Products': adjustment})
    invoice = {'Adjustments': enriched_adjustments}
    with open(ADJUSTMENT_FILE, 'w') as file:
        json.dump(invoice, file)
    print('Adjustments saved')


def main():
    service = get_service()
    raw_df = get_sheet_data(service)
    adjustments = extract_adjustments(raw_df)
    save_adjustments(adjustments)


if __name__ == '__main__':
    main()
