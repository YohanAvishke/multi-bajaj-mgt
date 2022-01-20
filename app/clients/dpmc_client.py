import requests
import logging

URL = "https://erp.dpg.lk/Help/GetHelp"
headers = {
    "authority": "erp.dpg.lk",
    "sec-ch-ua": "'Google Chrome';v='93', ' Not;A Brand';v='99', 'Chromium';v='93'",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
    "sec-ch-ua-mobile": "'?0'",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/93.0.4577.63 Safari/537.36",
    "sec-ch-ua-platform": "'macOS'",
    "origin": "https://erp.dpg.lk",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://erp.dpg.lk/Application/Home/PADEALER",
    "accept-language": "en-US,en;q=0.9",
    "dnt": "1",
    "sec-gpc": "1"
    }


def authenticate():
    payload = "strUserName=dlrmbenterp&strPassword=D0000402"
    headers["referer"] = "https://erp.dpg.lk/"

    response = requests.request("POST", "https://erp.dpg.lk/", headers = headers, data = payload)
    session = response.cookies._cookies['erp.dpg.lk']['/']['.AspNetCore.Session']
    cookie = f'{session.name}={session.value}'
    headers["cookie"] = cookie

    logging.info(f"Session created. Cookie: {headers['cookie']}")
    return cookie


def get_grn_from_column(column_name, number):
    payload = {
        "strInstance": "DLR",
        "strPremises": "KGL",
        "strAppID": "00011",
        "strFORMID": "00605",
        "strFIELD_NAME": ",STR_DEALER_CODE,STR_GRN_NO,STR_ORDER_NO,STR_INVOICE_NO,INT_TOTAL_GRN_VALUE",
        "strHIDEN_FIELD_INDEX": ",0",
        "strDISPLAY_NAME": ",STR_DEALER_CODE,GRN No,Order No,Invoice No,Total GRN Value",
        "strSearch": f"{number}",
        "strSEARCH_TEXT": "",
        "strSEARCH_FIELD_NAME": "STR_GRN_NO",
        "strColName": f"{column_name}",
        "strLIMIT": "0",
        "strARCHIVE": "TRUE",
        "strORDERBY": "STR_GRN_NO",
        "strOTHER_WHERE_CONDITION": "",
        "strAPI_URL": "api/Modules/Padealer/Padlrgoodreceivenote/List",
        "strTITEL": "",
        "strAll_DATA": "true",
        "strSchema": ""
        }

    response = requests.request("POST", URL, headers = headers, data = payload)

    if response.ok:
        return response.json()
    else:
        logging.error(f"GRN retrieval from column: {column_name} for number: {number} failed. Status: "
                      f"{response.status_code} for reason {response.text}")


def get_grn_from_mobile(mobile_number):
    payload = {
        "strInstance": "DLR",
        "strPremises": "KGL",
        "strAppID": "00011",
        "strFORMID": "00605",
        "strFIELD_NAME": ",DISTINCT STR_DLR_ORD_NO,STR_INVOICE_NO,STR_MOBILE_INVOICE_NO",
        "strHIDEN_FIELD_INDEX": "",
        "strDISPLAY_NAME": ",Order No,Invoice No,Mobile Invoice No",
        "strSearch": f"{mobile_number}",
        "strSEARCH_TEXT": "",
        "strSEARCH_FIELD_NAME": "STR_DLR_ORD_NO",
        "strColName": "STR_MOBILE_INVOICE_NO",
        "strLIMIT": "50",
        "strARCHIVE": "TRUE",
        "strORDERBY": "STR_DLR_ORD_NO",
        "strOTHER_WHERE_CONDITION": "",
        "strAPI_URL": "api/Modules/Padealer/Padlrgoodreceivenote/DealerPAPendingGRNNo",
        "strTITEL": "",
        "strAll_DATA": "true",
        "strSchema": ""
        }

    response = requests.request("POST", URL, headers = headers, data = payload)

    if response.ok:
        return response.json()
    else:
        logging.error(f"GRN retrieval from Mobile number: {mobile_number} failed. Status: {response.status_code} "
                      f"for reason {response.text}")


def get_grn_from_order(order_number):
    payload = {
        "strInstance": "DLR",
        "strPremises": "KGL",
        "strAppID": "00011",
        "strFORMID": "00605",
        "strFIELD_NAME": ",DISTINCT STR_DLR_ORD_NO,STR_INVOICE_NO,STR_MOBILE_INVOICE_NO",
        "strHIDEN_FIELD_INDEX": "",
        "strDISPLAY_NAME": ",Order No,Invoice No,Mobile Invoice No",
        "strSearch": "",
        "strSEARCH_TEXT": f"{order_number}",
        "strSEARCH_FIELD_NAME": "STR_DLR_ORD_NO",
        "strColName": "",
        "strLIMIT": "50",
        "strARCHIVE": "TRUE",
        "strORDERBY": "STR_DLR_ORD_NO",
        "strOTHER_WHERE_CONDITION": "",
        "strAPI_URL": "api/Modules/Padealer/Padlrgoodreceivenote/DealerPAPendingGRNNo",
        "strTITEL": "",
        "strAll_DATA": "true",
        "strSchema": ""
        }

    response = requests.request("POST", URL, headers = headers, data = payload)

    if response.ok:
        return response.json()
    else:
        logging.error(f"GRN retrieval from Mobile number: {order_number} failed. Status: {response.status_code} "
                      f"for reason {response.text}")


def advanced_grn_search(search_query):
    payload = {
        "strInstance": "DLR",
        "strPremises": "KGL",
        "strAppID": "00011",
        "strFORMID": "00605",
        "strFIELD_NAME": ",STR_DEALER_CODE,STR_GRN_NO,STR_ORDER_NO,STR_INVOICE_NO,INT_TOTAL_GRN_VALUE",
        "strHIDEN_FIELD_INDEX": ",0",
        "strDISPLAY_NAME": ",STR_DEALER_CODE,GRN No,Order No,Invoice No,Total GRN Value",
        "strSearch": f"{search_query['GRN search code']}",
        "strSEARCH_TEXT": "",
        "strSEARCH_FIELD_NAME": "STR_GRN_NO",
        "strColName": "STR_GRN_NO",
        "strLIMIT": "0",
        "strARCHIVE": "TRUE",
        "strORDERBY": "STR_GRN_NO",
        "strOTHER_WHERE_CONDITION": f"'+(+INT_TOTAL_GRN_VALUE%3D+'{search_query['GRN total']}'++)'",
        "strAPI_URL": "api/Modules/Padealer/Padlrgoodreceivenote/List",
        "strTITEL": "",
        "strAll_DATA": "true",
        "strSchema": ""
        }

    response = requests.request("POST", "https://erp.dpg.lk/Help/GetHelpForAdvanceSearch", headers = headers,
                                data = payload)
    if response.ok:
        return response.json()
    else:
        logging.error(f"GRN advance search for query: {search_query} failed. Status: {response.status_code} "
                      f"for reason {response.text}")


def get_products(invoice_number, grn_number):
    payload = {
        "STR_INSTANT": "DLR",
        "STR_PREMIS": "KGL",
        "STR_APP_ID": "00011",
        "STR_FORM_ID": "00605",
        "strMode": "GRN" if grn_number else "INVOICE",
        "STR_FUNCTION_ID": "IQ" if grn_number else "CR",
        "strInvoiceNo": f"{invoice_number}",
        "strPADealerCode": "AC2011063676"
        }

    if grn_number:
        payload["strGRNno"] = grn_number
    response = requests.request("POST", "https://erp.dpg.lk/PADEALER/PADLRGOODRECEIVENOTE/Inquire", headers = headers,
                                data = payload)
    if response.ok:
        return response.json()
    else:
        logging.error(f"Product retrieval for invoice: {invoice_number} failed. Status: {response.status_code} "
                      f"for reason {response.text}")


if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")
