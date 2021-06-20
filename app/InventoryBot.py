from datetime import date
import csv
import json
import requests
import logging
import pandas

# -*- File Paths -*-
INVOICE_PATH = "../data/inventory/invoices.json"
ADJUSTMENT_PATH = f"../data/inventory/adjustments/adjustment-{date.today()}.csv"
INVENTORY_PATH = "../data/inventory/product.inventory.line.csv"

# -*- Request URLs -*-
URL = "https://erp.dpg.lk/Help/GetHelp"
URL_PRODUCTS = "https://erp.dpg.lk/PADEALER/PADLRGOODRECEIVENOTE/Inquire"

# -*- Request Headers -*-
HEADERS = {
    "authority": "erp.dpg.lk",
    "sec-ch-ua": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "accept": "*/*",
    "x-requested-with": "XMLHttpRequest",
    "sec-ch-ua-mobile": "?0",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/90.0.4430.72 Mobile Safari/537.36",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://erp.dpg.lk",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://erp.dpg.lk/Application/Home/PADEALER",
    "accept-language": "en-US,en;q=0.9",
    "cookie": ".AspNetCore.Session=CfDJ8EFsLt37AbNMlnXZM"
              "%2FU7Qz6UpuTHfNhBbo7XQdke9XTDzk3kEYCZVrSma2RQHsu8wp9Jk16cixHxuFAz8WqbVhx3yQU2E2"
              "%2B1N48XXDmibRMWhVI7XWIWUbmzCku3g7h50uE6h50MQSU6BFXIy0H41%2BGrcjqtUByUcVbkMdqWHzmB; "
              ".AspNetCore.Antiforgery.mEZFPqlrlZ8"
              "=CfDJ8EFsLt37AbNMlnXZM_U7Qz6Xs4G4NFDO0KbM75EmpMPvdvf3HGsanEGbppclB5CtNVTrtq4--NxG"
              "-OLZsnPDtYPaVp_LiilPriuIEf4_jJW2o_WQUB-Qo-_hIRUIHuRKmAZo2oGBttwn0fOTiW3TbH8"
    }

# -*- Main function -*-
if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")


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
        response = requests.request("POST", URL, headers = HEADERS, data = payload)

        if response:
            invoice_details = json.loads(response.text)

            if invoice_details == "NO DATA FOUND":
                logging.info(f"Invoice Number: {invoice_number} has no data !!!")
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

    for number in invoice["Numbers"]:
        invoice_number = number["Invoice"]
        if "Sales" not in invoice_number:
            grn_number = number["GRN"] if "GRN" in number else None
            number["Products"] = []

            payload_mid = f"&strInvoiceNo={invoice_number}&strPADealerCode=AC2011063676&STR_FORM_ID=00605"
            payload = f"strMode=GRN&strGRNno={grn_number + payload_mid}&STR_FUNCTION_ID=IQ" \
                if grn_number else f"strMode=INVOICE{payload_mid}&STR_FUNCTION_ID=CR"
            payload = f"{payload}&STR_PREMIS=KGL&STR_INSTANT=DLR&STR_APP_ID=00011"

            response = requests.request("POST", URL_PRODUCTS, headers = HEADERS, data = payload)

            if response:
                product_details = json.loads(response.text)["DATA"]

                if product_details == "NO DATA FOUND":
                    logging.warning(f"Invoice Number: {number} is Invalid !!!")
                else:
                    product_details = product_details["dsGRNDetails"]["Table"] if "GRN" in number \
                        else product_details["dtGRNDetails"]

                    for product_detail in product_details:
                        number["Products"].append(product_detail)
            else:
                logging.error(
                    f'An error has occurred !!! \nStatus: {response.status_code} \nFor reason: {response.reason}')

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
    invoices = invoice_reader["Invoice"]["Numbers"]

    with open(ADJUSTMENT_PATH, "w") as adj_csv_file:
        field_names = ("name", "Product/Internal Reference", "Counted Quantity")
        adj_writer = csv.DictWriter(adj_csv_file, fieldnames = field_names, delimiter = ',', quotechar = '"',
                                    quoting = csv.QUOTE_MINIMAL)
        adj_writer.writeheader()

        for invoice in invoices:
            invoice_reference = invoice["Invoice"]

            for idx, product in enumerate(invoice["Products"]):
                product_number = product["STR_PART_NO"] if "STR_PART_NO" in product else product["STR_PART_CODE"]
                product_count = product["INT_QUANTITY"] if "INT_QUANTITY" in product else product["INT_QUATITY"]

                adj_writer.writerow({"name": invoice_reference,
                                     "Product/Internal Reference": product_number,
                                     "Counted Quantity": float(product_count)})

    merge_duplicates()
    logging.info("Product data modeling done.")


def merge_duplicates():
    # -*- coding: utf-8 -*-
    """
    Add the sum of the duplicate products
    """
    adjustment_reader = pandas.read_csv(ADJUSTMENT_PATH, header = 0)

    adjustment_reader["Counted Quantity"] = adjustment_reader.groupby(
        ["Product/Internal Reference"])["Counted Quantity"].transform('sum')
    adjustment_reader.drop_duplicates(subset = ["Product/Internal Reference"], inplace = True, keep = "last")

    adjustment_reader.to_csv(ADJUSTMENT_PATH, index = False)
    logging.info("Product duplicate merging done.")


def inventory_adjustment():
    # -*- coding: utf-8 -*-
    """ Before
    json_to_csv() should be called before to get the adjustment file

    After Call
    Final file to upload will be available at `ADJUSTMENT_PATH`
    """
    products = []
    previous_adjustment_invoice = None

    with open(INVENTORY_PATH, "r") as inventory_file, open(ADJUSTMENT_PATH, "r") as adjustment_file:
        inventory_reader = list(csv.DictReader(inventory_file))
        adjustment_reader = list(csv.DictReader(adjustment_file))

    for adjustment_product in adjustment_reader:
        exists = False
        adjustment_invoice = adjustment_product["name"]
        is_exhausted_included = True
        adjustment_number = adjustment_product["Product/Internal Reference"]
        adjustment_quantity = float(adjustment_product["Counted Quantity"])

        if adjustment_invoice == previous_adjustment_invoice:
            adjustment_invoice = None
            is_exhausted_included = None
        previous_adjustment_invoice = adjustment_product["name"]

        for inventory_product in inventory_reader:
            inventory_number = inventory_product["Product/Internal Reference"]
            inventory_quantity = float(inventory_product["Quantity On Hand"])

            if adjustment_number == inventory_number:
                exists = True
                products.append({
                    "name": f"Invoice Number - {adjustment_invoice}",
                    "Include Exhausted Products": is_exhausted_included,
                    "line_ids/product_id/id": inventory_product["Product/ID"],
                    "line_ids/location_id/id": "stock.stock_location_stock",
                    "line_ids/product_qty": inventory_quantity + adjustment_quantity,
                    })
                break

        if not exists:
            logging.warning(f"Product Number: {adjustment_number} is Invalid !!!")

    with open(ADJUSTMENT_PATH, mode = 'w') as adjustment_file:
        field_names = ("name", "Include Exhausted Products", "line_ids/product_id/id", "line_ids/location_id/id",
                       "line_ids/product_qty")
        adjustment_writer = csv.DictWriter(adjustment_file, fieldnames = field_names, delimiter = ',', quotechar = '"',
                                           quoting = csv.QUOTE_MINIMAL)
        adjustment_writer.writeheader()

        for product in products:
            adjustment_writer.writerow(product)

    logging.info("Inventory Adjustment done.")


# -*- Function Calls -*-
# get_grn_for_invoice()
# get_products_from_invoices()
# json_to_csv()
# merge_duplicates()
# inventory_adjustment()
