import csv
import json
import requests

INVOICE_PATH = "../data/inventory/invoices.json"
ADJUSTMENT_JSON_PATH = "../data/inventory/adjustments/adjustment-21:04:29,30.json"
ADJUSTMENT_CSV_PATH = "../data/inventory/adjustments/adjustment-21:04:29,30.csv"

URL_INVOICE = "https://erp.dpg.lk/Help/GetHelp"
URL_PRODUCTS = "https://erp.dpg.lk/PADEALER/PADLRGOODRECEIVENOTE/Inquire"

HEADERS = {
    'authority': 'erp.dpg.lk',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/90.0.4430.93 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://erp.dpg.lk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': '.AspNetCore.Session=CfDJ8N8gIs%2FXx8JIrXltjeQ28vGUovewhiCGa7dBuOOJEHlraIPQTMUBK7cCBgs%2ByZUcbHVSJ6'
              'kozamdoMdGQogLFEX7NUdaFd8TKnQdHMkE7LjNuEwMTCHizHN2yzUB5wz8N9raKnEPvYPx5xRsjlWM%2BySf2yupM3k7kxtv7sN'
              'Ob0cz; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8N8gIs_Xx8JIrXltjeQ28vHnbaej-dcUfNA-e_pAj5cHEKQI3eKb'
              'nurde3xlktWSsMzzMjv3MYTvLXIV2HxB7g0xmG_P7wDzQ0iRsQnkJw43kvDjwv-qGjKzDvKq_cmnD8x_n_P-g43sm9BR2n_dKaw'
}


def get_invoices():
    with open(INVOICE_PATH, "r") as invoice_file:
        invoice_reader = json.load(invoice_file)
    invoice = invoice_reader["Invoice"]

    for head in invoice["Heads"]:
        payload = "strInstance=DLR&strPremises=KGL&strAppID=00011&strFORMID=00605&" \
                  "strFIELD_NAME=%2CSTR_DEALER_CODE%2CSTR_GRN_NO%2CSTR_ORDER_NO%2CSTR_INVOICE_NO%2" \
                  "CINT_TOTAL_GRN_VALUE&strHIDEN_FIELD_INDEX=%2C0&strDISPLAY_NAME=%2CSTR_DEALER_CODE%2CGRN+No%2COrder" \
                  f"+No%2CInvoice+No%2CTotal+GRN+Value&strSearch={head}&strSEARCH_TEXT=&" \
                  "strSEARCH_FIELD_NAME=STR_GRN_NO&strColName=STR_INVOICE_NO&strLIMIT=50&strARCHIVE=TRUE&" \
                  "strORDERBY=STR_GRN_NO&strOTHER_WHERE_CONDITION=%5B%5B%22STR_DEALER_CODE+%22%2C%22%3D%22%2C%22'" \
                  "AC2011063676'%22%5D%5D&strAPI_URL=api%2FModules%2FPadealer%2FPadlrgoodreceivenote%2FList&" \
                  "strTITEL=&strAll_DATA=true&strSchema="
        response = requests.request("POST", URL_INVOICE, headers=HEADERS, data=payload)
        numbers = json.loads(response.text)

        invoice["Numbers"] = numbers

    with open(INVOICE_PATH, "w") as invoice_file:
        json.dump(invoice_reader, invoice_file)


def get_products():
    with open(INVOICE_PATH, "r") as invoice_file:
        invoice_reader = json.load(invoice_file)
    invoice = invoice_reader["Invoice"]

    for number in invoice["Numbers"]:
        grn_number = number["GRN No"]
        invoice_number = number["Invoice No"]

        payload = "strMode=GRN&" \
                  f"strGRNno={grn_number}&strInvoiceNo={invoice_number}&" \
                  "strPADealerCode=AC2011063676&STR_FORM_ID=00605&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&" \
                  "STR_INSTANT=DLR&STR_APP_ID=00011"
        response = requests.request("POST", URL_PRODUCTS, headers=HEADERS, data=payload)

        print(response.text)
        break


def json_to_csv():
    with open(ADJUSTMENT_JSON_PATH, "r") as adj_json_file:
        adj_reader = json.load(adj_json_file)

    with open(ADJUSTMENT_CSV_PATH, "w") as adj_csv_file:
        field_names = ("Product/Internal Reference", "Counted Quantity")
        adj_writer = csv.DictWriter(adj_csv_file, fieldnames=field_names, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
        adj_writer.writeheader()

        for product in adj_reader:
            product_number = product["STR_PART_NO"] if "STR_PART_NO" in product else product["STR_PART_CODE"]
            product_count = product["INT_QUANTITY"] if "INT_QUANTITY" in product else product["INT_QUATITY"]

            adj_writer.writerow({"Product/Internal Reference": product_number, "Counted Quantity": product_count})


# get_invoices()
# get_products()
json_to_csv()
