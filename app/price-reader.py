import requests
import json
import time

url = "https://erp.dpg.lk/PADEALER/PADLRItemInquiry/Inquire"

headers = {
    'authority': 'erp.dpg.lk',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'accept': '*/*',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                  '89.0.4389.114 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://erp.dpg.lk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': '.AspNetCore.Session=CfDJ8H8TYQJVgJRGttyTw7gWFEZoDWDrYJsPTYLKqZdcoYdyYhG3ggsoMRkYnL7V1g5pLuXUNpLdOeaUW%2BLAIHd0Mrvle4KtcFHJ0nGqyZZnOCzkUmX6obnOebX30RNKAj%2FkJH%2BMQ8%2FRZKmkxhoPrFIG9pB%2FcpmD5jNd8qRZMe4IsxYh; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8H8TYQJVgJRGttyTw7gWFEawVVW-1-ZcXNH31kg-kamO9B4yfGVKSI5EoxMByzV1CoJk8oA0Qp0mCkNsTqWsvRJtpTyagST5kjTPd5icsGtdPabpCxdvOnAGunsuP6OON-nDcPMTAuqmmNg8NfNS0k0'
}

numbers = [
    'JK122002',
    'Y-Flash Armature',
    'JD551206',
    '39100006',
    'DK101503',
    'Y-Pulsar Kick Padel',
    'Y-CT-100 gear Pedal',
    'Y-Discover Brake Cable',
    'Y-2S Petrol Cap',
    'Y-ARC-Brake Washer [R]',
    'Y-ARC-Brake Rake Washer [F]',
    'GF201009',
    'YPA13001',
    'DT511261',
    'DJ121064',
    'Y-DU191005 Clamp',
    ' DJ121064',
    'Y-Varroc Brush Set',
    '36JZ0007',
    'DJ201132',
    'AA101814',
    '22191096',
    '24101056',
    '24131046',
    '24191182',
    '36DK0015',
    'AA111107',
    'AN101152',
    'DP101107',
    'JE511230',
]

for number in numbers:
    payload = f'strPartNo_PAItemInq={number}&strFuncType=INVENTORYDATA&strPADealerCode_PAItemInq=AC2011063676&STR_' \
              f'FORM_ID=00602&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&STR_INSTANT=DLR&STR_APP_ID=00011'

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        data = json.loads(response.text)['DATA']

        if 'dblSellingPrice' in data:
            print(data['dblSellingPrice'])
        else:
            print(f'{number} - Not Found.')
    else:
        print(f'{number} - Not Found.')
