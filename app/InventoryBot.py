from datetime import date
import csv
import json
import requests
import logging
import pandas

# -*- File Paths -*-
INVOICE_PATH = "../data/inventory/invoices.json"
ADJUSTMENT_PATH = f"../data/inventory/adjustments/adjustment-{date.today()}.2.csv"
INVENTORY_PATH = "../data/inventory/product.inventory.csv"

# -*- Request URLs -*-
URL = "https://erp.dpg.lk/Help/GetHelp"
URL_PRODUCTS = "https://erp.dpg.lk/PADEALER/PADLRGOODRECEIVENOTE/Inquire"
ULR_ADVANCED = "https://erp.dpg.lk/Help/GetHelpForAdvanceSearch"

# -*- Constants -*-
HEADERS = {
    'authority': 'erp.dpg.lk',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/91.0.4472.114 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://erp.dpg.lk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': '.AspNetCore.Session=CfDJ8DRqtPu%2Be5FAgn%2BoZH10nKaxMi32BYoqJsUnBd%2F22%2FjS9Nt1M4'
              '%2BmGzIakx7xwbUpfrJ8t92%2Bh4dzPGYW%2FWqY2bTg9KmqrlatAnv2aIJfHsSv0TOj6AAPv5oskDK4VzvcAL%2FM'
              '%2BNBbYiLfj8NtaElcyJHJCgMn6X4VQ44sW8jye3Al; '
              '.AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8DRqtPu-e5FAgn-oZH10nKbOovYUTQOE_WjC-iv9KSo3AmE8cn1c0'
              '-wHIuhyQGCCfBjxT2RL2heeAVP_7-b6ECjHicA7gvnz632KBADvgGyXEGej_aUvwz96cRF3bd_WSgnTfDN88ONAoUfdClUCrI8',
    'dnt': '1',
    'sec-gpc': '1'
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
        col_name = None
        id_type = number["Type"]

        if "Other" not in id_type and "Missing" not in id_type:
            invoice_id = number["ID"]
            if "Invoice" in id_type:
                col_name = "STR_INVOICE_NO"
            elif "Order" in id_type:
                col_name = "STR_ORDER_NO"

            payload = "strInstance=DLR&" \
                      "strPremises=KGL&" \
                      "strAppID=00011&" \
                      "strFORMID=00605&" \
                      "strFIELD_NAME=%2CSTR_DEALER_CODE%2CSTR_GRN_NO%2CSTR_ORDER_NO%2CSTR_INVOICE_NO" \
                      "%2CINT_TOTAL_GRN_VALUE&" \
                      "strHIDEN_FIELD_INDEX=%2C0&" \
                      "strDISPLAY_NAME=%2CSTR_DEALER_CODE%2CGRN+No%2COrder+No%2CInvoice+No%2CTotal+GRN+Value&" \
                      f"strSearch={invoice_id}&" \
                      f"strSEARCH_TEXT=&" \
                      f"strSEARCH_FIELD_NAME=STR_GRN_NO&" \
                      f"strColName={col_name}&" \
                      f"strLIMIT=0&" \
                      f"strARCHIVE=TRUE&" \
                      f"strORDERBY=STR_GRN_NO&" \
                      f"strOTHER_WHERE_CONDITION=&" \
                      f"strAPI_URL=api%2FModules%2FPadealer%2FPadlrgoodreceivenote%2FList&" \
                      f"strTITEL=&" \
                      f"strAll_DATA=true" \
                      f"&strSchema="
            response = requests.request("POST", URL, headers = HEADERS, data = payload)

            if response:
                invoice_details = json.loads(response.text)

                if invoice_details == "NO DATA FOUND":
                    logging.info(f"Invoice Number: {invoice_id} has no data !!!")
                elif len(invoice_details) > 1:
                    logging.info(f"Invoice Number: {invoice_id} is too Vague !!!")
                else:
                    number["GRN"] = invoice_details[0]["GRN No"]
                    if "Order" in id_type:
                        number["ID"] = invoice_details[0]["Invoice No"]
            else:
                logging.error(
                    f'An error has occurred !!! \nStatus: {response.status_code} \nFor reason: {response.reason}')
        elif "Missing" in id_type:
            get_missing_invoice_id(number)

    with open(INVOICE_PATH, "w") as invoice_file:
        json.dump(invoice_reader, invoice_file)

    logging.info("Invoice data scrapping done.")


def get_missing_invoice_id(details):
    # -*- coding: utf-8 -*-
    payload = "strInstance=DLR&" \
              "strPremises=KGL&" \
              "strAppID=00011&" \
              "strFORMID=00605&" \
              "strFIELD_NAME=%2CSTR_DEALER_CODE%2CSTR_GRN_NO%2CSTR_ORDER_NO%2CSTR_INVOICE_NO%2CINT_TOTAL_GRN_VALUE&" \
              "strHIDEN_FIELD_INDEX=%2C0&" \
              "strDISPLAY_NAME=%2CSTR_DEALER_CODE%2CGRN+No%2COrder+No%2CInvoice+No%2CTotal+GRN+Value&" \
              f"strSearch={details['GRN search code']}&" \
              "strSEARCH_TEXT=&" \
              "strSEARCH_FIELD_NAME=STR_GRN_NO&" \
              "strColName=STR_GRN_NO&" \
              "strLIMIT=0&" \
              "strARCHIVE=TRUE&" \
              "strORDERBY=STR_GRN_NO&" \
              f"strOTHER_WHERE_CONDITION=+(+INT_TOTAL_GRN_VALUE%3D+'{details['GRN total']}'++)&" \
              "strAPI_URL=api%2FModules%2FPadealer%2FPadlrgoodreceivenote%2FList&" \
              "strTITEL=&" \
              "strAll_DATA=true&" \
              "strSchema="

    response = requests.request("POST", ULR_ADVANCED, headers = HEADERS, data = payload)
    invoice_details = json.loads(response.text)

    if invoice_details == "NO DATA FOUND":
        logging.warning(
            f"Missing data retreival failed for search code: {details['GRN search code']} and value "
            f"{details['GRN total']}")
    else:
        if len(invoice_details) == 1:
            details["ID"] = invoice_details[0]["Invoice No"]
            details["GRN"] = invoice_details[0]["GRN No"]
        else:
            details["Retrieved Data"] = invoice_details
            logging.warning(
                f"Missing data has multiple records. Details: {details['GRN search code']} and value "
                f"{details['GRN total']}")


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
        id_type = number["Type"]

        if "Other" not in id_type and "Missing" not in id_type:
            invoice_id = number["ID"]
            grn_number = number["GRN"] if "GRN" in number else None
            number["Products"] = []

            payload_mid = f"&strInvoiceNo={invoice_id}&strPADealerCode=AC2011063676&STR_FORM_ID=00605"
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
        elif "Missing" in id_type:
            logging.warning("Invoice with missing identifiers are still present.")

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
            invoice_reference = invoice["ID"]

            for idx, product in enumerate(invoice["Products"]):
                product_number = product["STR_PART_NO"] if "STR_PART_NO" in product else product["STR_PART_CODE"]
                product_count = product["INT_QUANTITY"] if "INT_QUANTITY" in product else product["INT_QUATITY"]

                adj_writer.writerow({"name": invoice_reference,
                                     "Product/Internal Reference": product_number,
                                     "Counted Quantity": float(product_count)})
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
    invalid_products = []
    previous_adjustment_invoice = None

    with open(INVENTORY_PATH, "r") as inventory_file, open(ADJUSTMENT_PATH, "r") as adjustment_file:
        inventory_reader = list(csv.DictReader(inventory_file))
        adjustment_reader = list(csv.DictReader(adjustment_file))

    for adjustment_product in adjustment_reader:
        adjustment_invoice = adjustment_product["name"]
        is_exhausted_included = True

        adjustment_number = adjustment_product["Product/Internal Reference"]
        adjustment_quantity = float(adjustment_product["Counted Quantity"])
        exists = False

        if adjustment_invoice == previous_adjustment_invoice:
            adjustment_invoice = None
            is_exhausted_included = None

        for inventory_product in inventory_reader:
            inventory_number = inventory_product["Internal Reference"]
            inventory_quantity = float(inventory_product["Quantity On Hand"])

            if adjustment_number == inventory_number:
                exists = True
                finalised_quantity = inventory_quantity + adjustment_quantity

                if inventory_quantity < 0:
                    logging.warning(f"Inventory initial qty is negative: {adjustment_number}."
                                    f"Inventory: {inventory_quantity}. Difference: {adjustment_quantity} . Finalised "
                                    f"qty: {finalised_quantity}.")
                elif finalised_quantity < 0:
                    logging.warning(f"Inventory final qty is negative: {adjustment_number}."
                                    f"Inventory: {inventory_quantity}. Difference: {adjustment_quantity}. Finalised "
                                    f"qty: {finalised_quantity}.")

                products.append({
                    "name": adjustment_invoice,
                    "Include Exhausted Products": is_exhausted_included,
                    "reference": inventory_number,
                    "line_ids/product_id/id": inventory_product["Product/Product/ID"],
                    "line_ids/location_id/id": "stock.stock_location_stock",
                    "line_ids/product_qty": finalised_quantity,
                    })
                # Update `previous_adjustment_invoice` if `adjustment_invoice` is valid and exists
                previous_adjustment_invoice = adjustment_product["name"]

                break

        if not exists:
            invalid_products.append(adjustment_product)

    for product in invalid_products:
        logging.error(f"Product Number: {product['Product/Internal Reference']} is Invalid !!!")

    with open(ADJUSTMENT_PATH, mode = 'w') as adjustment_file:
        field_names = (
            "name", "Include Exhausted Products", "reference", "line_ids/product_id/id", "line_ids/location_id/id",
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
json_to_csv()
merge_duplicates()
inventory_adjustment()
