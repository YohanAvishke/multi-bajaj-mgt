import requests
import json

URL = "https://erp.dpg.lk/Help/GetHelp"
HEADERS = {
    'authority': 'erp.dpg.lk',
    'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/93.0.4577.63 Safari/537.36',
    'sec-ch-ua-platform': '"macOS"',
    'origin': 'https://erp.dpg.lk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': '.AspNetCore.Session=CfDJ8Nf%2BuJSs619Ej1a3tttZRKQjjdmyGrpZnx8%2FKLC'
              '%2FcXTjbj3PQEnkzIR0jIwkKYIYwEnhUtrG2dFjxdzcMIn4BOE9%2F3ChFH0%2BV3xoRs5sMx7oTsKa0DkzqU'
              '%2FxGKRuWgGXhlpLvnyFyepdC2aA5o40jy5JDtC6xqJF3fj%2BN5S0P6TE; '
              '.AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8Nf'
              '-uJSs619Ej1a3tttZRKS7HXtDuDYpom0z69xVQwr4yeAS3GsNJwivd0SLipkRE11dfenSY__3u0'
              '-PSePBoj0OzhZu1nVvW4pz4_UvZYp5lxK5crI6AgReoXnF5rmAtk5KnU36a3Xd1QoYC4iV51g',
    'dnt': '1',
    'sec-gpc': '1'
    }


def filter_from_mobile_number(mobile_number):
    payload = "strInstance=DLR&" \
              "strPremises=KGL&" \
              "strAppID=00011&" \
              "strFORMID=00605&" \
              "strFIELD_NAME=%2CDISTINCT+STR_DLR_ORD_NO%2CSTR_INVOICE_NO%2CSTR_MOBILE_INVOICE_NO&" \
              "strHIDEN_FIELD_INDEX=&" \
              "strDISPLAY_NAME=%2COrder+No%2CInvoice+No%2CMobile+Invoice+No&" \
              f"strSearch={mobile_number}&" \
              "strSEARCH_TEXT=&" \
              "strSEARCH_FIELD_NAME=STR_DLR_ORD_NO&" \
              "strColName=STR_MOBILE_INVOICE_NO&" \
              "strLIMIT=50&" \
              "strARCHIVE=TRUE&" \
              "strORDERBY=STR_DLR_ORD_NO&" \
              "strOTHER_WHERE_CONDITION=&" \
              "strAPI_URL=api%2FModules%2FPadealer%2FPadlrgoodreceivenote%2FDealerPAPendingGRNNo&" \
              "strTITEL=&" \
              "strAll_DATA=true&" \
              "strSchema="
    response = requests.request("POST", URL, headers = HEADERS, data = payload)
    return json.loads(json.loads(response.text))


def filter_from_order_number(order_number):
    payload = {
        'strInstance': 'DLR',
        'strPremises': 'KGL',
        'strAppID': '00011',
        'strFORMID': '00605',
        'strFIELD_NAME': ',DISTINCT STR_DLR_ORD_NO,STR_INVOICE_NO,STR_MOBILE_INVOICE_NO',
        'strHIDEN_FIELD_INDEX': '',
        'strDISPLAY_NAME': ',Order No,Invoice No,Mobile Invoice No',
        'strSearch': '',
        'strSEARCH_TEXT': f'{order_number}',
        'strSEARCH_FIELD_NAME': 'STR_DLR_ORD_NO',
        'strColName': '',
        'strLIMIT': '50',
        'strARCHIVE': 'TRUE',
        'strORDERBY': 'STR_DLR_ORD_NO',
        'strOTHER_WHERE_CONDITION': '',
        'strAPI_URL': 'api/Modules/Padealer/Padlrgoodreceivenote/DealerPAPendingGRNNo',
        'strTITEL': '',
        'strAll_DATA': 'true',
        'strSchema': ''
        }
    response = requests.request("POST", URL, headers = HEADERS, data = payload)
    # 2 fucking strings
    return json.loads(json.loads(response.text))
