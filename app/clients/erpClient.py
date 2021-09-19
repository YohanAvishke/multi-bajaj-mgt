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
    'cookie': '.AspNetCore.Session=CfDJ8Kni6SCm82FNnaxek0dcFoQowZqAboDUA9QXwZrNzIzNXrEBh5XWR6SHCMsapggoStdajY7Vj863s1'
              'fShXtZnw1jjB5bvI4ySWupVGmDNGKgam6xO1AqoR%2FExONkc7uedAR6x8eTtMGXbXYT5S%2BDNJcTD5D1gkaB2V%2FX25KAW%2FU%'
              '2B; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8Kni6SCm82FNnaxek0dcFoQwG0743sXKK3Kf1yJHETtNEuUJm23e-bE4wn'
              'dTQsvwN1GVPB7Kf6OxtMuOLUKS1fxJ1FPi9DuCXEPh77qqWWyivhZ3TLAQ9HKbhQysToBKXOT0vaUVuS-nE4EZ5Lirzws',
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
    return json.loads(response.text)
