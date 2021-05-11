import csv
import json
import requests
import logging

# -*- File Paths -*-
INVOICE_PATH = "../data/inventory/invoices.json"
ADJUSTMENT_PATH = "../data/inventory/adjustments/adjustment-21:04:29,30.csv"
INVENTORY_PATH = "../data/inventory/stock.inventory.line.csv"

# -*- Request URLs -*-
URL = "https://erp.dpg.lk/Help/GetHelp"
URL_PRODUCTS = "https://erp.dpg.lk/PADEALER/PADLRGOODRECEIVENOTE/Inquire"

# -*- Request Headers -*-
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

# -*- Main function -*-
if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")


# -*- Functions -*-
def get_grn_for_invoice():
    # -*- coding: utf-8 -*-
    """ Before
    Add the Invoice numbers to ['Invoice']['Numbers']['Invoice']

    ``` After
    Call get_products_from_invoices()
    """
    with open(INVOICE_PATH, "r") as invoice_file:
        invoice_reader = json.load(invoice_file)
    invoice = invoice_reader["Invoice"]

    for number in invoice["Numbers"]:
        invoice_number = number["Invoice"]

        payload = "strInstance=DLR&strPremises=KGL&strAppID=00011&strFORMID=00605&strFIELD_NAME=%2CSTR_DEALER_CODE" \
                  "%2CSTR_GRN_NO%2CSTR_ORDER_NO%2CSTR_INVOICE_NO%2CINT_TOTAL_GRN_VALUE&strHIDEN_FIELD_INDEX=%2C0&" \
                  "strDISPLAY_NAME=%2CSTR_DEALER_CODE%2CGRN+No%2COrder+No%2CInvoice+No%2CTotal+GRN+Value&" \
                  f"strSearch={invoice_number}&strSEARCH_TEXT=&strSEARCH_FIELD_NAME=STR_GRN_NO&" \
                  "strColName=STR_INVOICE_NO&strLIMIT=50&strARCHIVE=TRUE&strORDERBY=STR_GRN_NO&" \
                  "strOTHER_WHERE_CONDITION=%5B%5B%22STR_DEALER_CODE+%22%2C%22%3D%22%2C%22'AC2011063676'%22%5D%5D&" \
                  "strAPI_URL=api%2FModules%2FPadealer%2FPadlrgoodreceivenote%2FList&strTITEL=&strAll_DATA=true&" \
                  "strSchema="
        response = requests.request("POST", URL, headers=HEADERS, data=payload)

        if response:
            invoice_details = json.loads(response.text)

            if invoice_details == "NO DATA FOUND":
                logging.info(f"Invoice Number: {invoice_number} is Invalid !!!")
            elif len(invoice_details) > 1:
                logging.info(f"Invoice Number: {invoice_number} is too Vague !!!")
            else:
                number["GRN"] = invoice_details[0]["GRN No"]
        else:
            logging.error(f'An error has occurred !!! \nStatus: {response.status_code} \nFor reason: {response.reason}')

    with open(INVOICE_PATH, "w") as invoice_file:
        json.dump(invoice_reader, invoice_file)

    logging.info("Invoice data scrapping done.")


def get_products_from_invoices():
    # -*- coding: utf-8 -*-
    """ Before
    get_grn_for_invoice() should be called before

    ''' After Call
    Part Numbers are located at ['Invoice']['Products']
    """
    with open(INVOICE_PATH, "r") as invoice_file:
        invoice_reader = json.load(invoice_file)
    invoice = invoice_reader["Invoice"]
    invoice["Products"] = []

    for number in invoice["Numbers"]:
        invoice_number = number["Invoice"]
        grn_number = number["GRN"] if "GRN" in number else None

        payload_mid = f"&strInvoiceNo={invoice_number}&strPADealerCode=AC2011063676&STR_FORM_ID=00605"
        payload = f"strMode=GRN&strGRNno={grn_number + payload_mid}&STR_FUNCTION_ID=IQ" \
            if grn_number else f"strMode=INVOICE{payload_mid}&STR_FUNCTION_ID=CR"
        payload = f"{payload}&STR_PREMIS=KGL&STR_INSTANT=DLR&STR_APP_ID=00011"

        response = requests.request("POST", URL_PRODUCTS, headers=HEADERS, data=payload)

        if response:
            product_details = json.loads(response.text)["DATA"]

            if product_details == "NO DATA FOUND":
                logging.warning(f"Invoice Number: {number} is Invalid !!!")
            else:
                product_details = product_details["dsGRNDetails"]["Table"] if "GRN" in number \
                    else product_details["dtGRNDetails"]

                for product_detail in product_details:
                    invoice["Products"].append(product_detail)
        else:
            logging.error(f'An error has occurred !!! \nStatus: {response.status_code} \nFor reason: {response.reason}')

    with open(INVOICE_PATH, "w") as invoice_file:
        json.dump(invoice_reader, invoice_file)

    logging.info("Product data scrapping done.")


def json_to_csv():
    # -*- coding: utf-8 -*-
    """ Before
    get_products_from_invoices() should be called before

    ''' After Call
    Part Numbers with the quantities will be in the `ADJUSTMENT_PATH`
    """
    with open(INVOICE_PATH, "r") as invoice_file:
        invoice_reader = json.load(invoice_file)
    products = invoice_reader["Invoice"]["Products"]

    with open(ADJUSTMENT_PATH, "w") as adj_csv_file:
        field_names = ("Product/Internal Reference", "Counted Quantity")
        adj_writer = csv.DictWriter(adj_csv_file, fieldnames=field_names, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)
        adj_writer.writeheader()

        for product in products:
            product_number = product["STR_PART_NO"] if "STR_PART_NO" in product else product["STR_PART_CODE"]
            product_count = product["INT_QUANTITY"] if "INT_QUANTITY" in product else product["INT_QUATITY"]

            adj_writer.writerow({"Product/Internal Reference": product_number,
                                 "Counted Quantity": float(product_count)})

    logging.info("Product data modeling done.")


def inventory_adjustment():
    # -*- coding: utf-8 -*-
    """ Before
    json_to_csv() should be called before to get the adjustment file

    After Call
    Final file to upload will be available at `ADJUSTMENT_PATH`
    """
    products = []

    with open(INVENTORY_PATH, "r") as inventory_file, open(ADJUSTMENT_PATH, "r") as adjustment_file:
        inventory_reader = list(csv.DictReader(inventory_file))
        adjustment_reader = list(csv.DictReader(adjustment_file))

    for adjustment_product in adjustment_reader:
        exists = False
        adjustment_number = adjustment_product["Product/Internal Reference"]
        adjustment_quantity = float(adjustment_product["Counted Quantity"])

        for inventory_product in inventory_reader:
            inventory_number = inventory_product["Product/Internal Reference"]
            inventory_quantity = float(inventory_product["Counted Quantity"])

            if adjustment_number == inventory_number:
                exists = True
                inventory_product["Counted Quantity"] = inventory_quantity + adjustment_quantity
                products.append(inventory_product)
                break

        if not exists:
            logging.warning(f"Product Number: {adjustment_number} is Invalid !!!")

    with open(ADJUSTMENT_PATH, mode='w') as adjustment_file:
        field_names = ("ID", "Product/ID", "Product/Internal Reference", "Counted Quantity")
        adjustment_writer = csv.DictWriter(adjustment_file, fieldnames=field_names, delimiter=',', quotechar='"',
                                           quoting=csv.QUOTE_MINIMAL)
        adjustment_writer.writeheader()

        for product in products:
            adjustment_writer.writerow(product)

    logging.info("Inventory Adjustment done.")


# -*- Function Calls -*-
# get_grn_for_invoice()
# get_products_from_invoices()
# json_to_csv()
# inventory_adjustment()
