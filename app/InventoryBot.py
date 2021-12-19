from __future__ import print_function, unicode_literals

from datetime import date
from app.config import ROOT_DIR

import re
import csv
import json
import requests
import logging
import pandas as pd
import app.dpmc as dpmc
import app.googlesheet as sheet

# -*- Dir Paths -*-
INV_DIR = f'{ROOT_DIR}/data/inventory'
ADJ_DIR = f'{INV_DIR}/adjustments'
# -*- File Paths -*-
ADJ_DPMC_FILE = f'{INV_DIR}/adjustment.dpmc.json'
ADJ_OTHER_FILE = f'{INV_DIR}/adjustment.other.json'
INVENTORY_FILE = f'{INV_DIR}/product.inventory.csv'
SALES_PATH = f'{INV_DIR}/sales.xlsx'
FIX_FILE = f'{ADJ_DIR}/{date.today()}-fix.csv'
DATED_ADJUSTMENT_FILE = f'{ADJ_DIR}/{date.today()}-adjustment.csv'

# -*- Request -*-
URL = 'https://erp.dpg.lk/Help/GetHelp'
URL_PRODUCTS = 'https://erp.dpg.lk/PADEALER/PADLRGOODRECEIVENOTE/Inquire'
ULR_ADVANCED = 'https://erp.dpg.lk/Help/GetHelpForAdvanceSearch'
# -*- Headers -*-
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
    'dnt': '1',
    'sec-gpc': '1'
    }
# -*- Payloads -*-
PAYLOAD = {
    'strInstance': 'DLR&',
    'strPremises': 'KGL&',
    'strAppID': '00011&',
    'strFORMID': '00605&',
    'strFIELD_NAME': '%2CSTR_DEALER_CODE%2CSTR_GRN_NO%2CSTR_ORDER_NO%2CSTR_INVOICE_NO%2CINT_TOTAL_GRN_VALUE&',
    'strHIDEN_FIELD_INDEX': '%2C0&',
    'strDISPLAY_NAME': '%2CSTR_DEALER_CODE%2CGRN+No%2COrder+No%2CInvoice+No%2CTotal+GRN+Value&',
    'strSEARCH_TEXT': '&',
    'strSEARCH_FIELD_NAME': 'STR_GRN_NO&',
    'strLIMIT': '0&',
    'strARCHIVE': 'TRUE&',
    'strORDERBY': 'STR_GRN_NO&',
    'strOTHER_WHERE_CONDITION': '&',
    'strAPI_URL': 'api%2FModules%2FPadealer%2FPadlrgoodreceivenote%2FList&',
    'strTITEL': '&',
    'strAll_DATA': 'true',
    '&strSchema': ''
    }


def main():
    adjustments = pd.read_json(ADJ_DPMC_FILE, orient = 'records').Adjustments.to_list()
    adjustment_df = pd.json_normalize(adjustments)


def get_grn_for_invoice():
    with open(ADJ_DPMC_FILE, "r") as invoice_file:
        invoice_reader = json.load(invoice_file)
    adjustments = invoice_reader["Adjustments"]

    for adjustment in adjustments:
        adj_type = adjustment["Type"]

        if "DPMC" in adj_type:
            if "Missing" in adj_type:
                get_missing_invoice_id(adjustment)
                continue

            adj_ref = adjustment["ID"]
            if "Invoice" in adj_type:
                col_name = "STR_INVOICE_NO"
            else:
                if "Order" in adj_type:
                    data = dpmc.filter_from_order_number(adj_ref)
                else:
                    data = dpmc.filter_from_mobile_number(adj_ref)

                if len(data) != 1:
                    adjustment["Type"] = "DPMC/Missing"
                    logging.warning(f"get_grn_for_invoice filtering failed for {adj_ref}\n {data}")
                    continue
                else:
                    data = data[0]
                    if data["Invoice No"] != "":
                        adjustment["ID"] = data["Invoice No"]
                        adjustment["Type"] = "DPMC/Invoice"
                        col_name = "STR_INVOICE_NO"
                    elif data["Order No"] != "":
                        adjustment["ID"] = data["Order No"]
                        adjustment["Type"] = "DPMC/Order"
                        col_name = "STR_ORDER_NO"
                    else:
                        adjustment["Type"] = "DPMC/Missing"
                        logging.warning(f"get_grn_for_invoice filtered data invalid for {adj_ref}\n {data}")
                        continue

            payload = "strInstance=DLR&" \
                      "strPremises=KGL&" \
                      "strAppID=00011&" \
                      "strFORMID=00605&" \
                      "strFIELD_NAME=%2CSTR_DEALER_CODE%2CSTR_GRN_NO%2CSTR_ORDER_NO%2CSTR_INVOICE_NO" \
                      "%2CINT_TOTAL_GRN_VALUE&" \
                      "strHIDEN_FIELD_INDEX=%2C0&" \
                      "strDISPLAY_NAME=%2CSTR_DEALER_CODE%2CGRN+No%2COrder+No%2CInvoice+No%2CTotal+GRN+Value&" \
                      f"strSearch={adj_ref}&" \
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
                    logging.warning(f"Invoice Number: {adj_ref} has no data !!!")
                    continue
                elif type(invoice_details) is str:
                    invoice_details = json.loads(invoice_details)
                elif len(invoice_details) > 1:
                    logging.warning(f"Invoice Number: {adj_ref} is too Vague !!!")
                    continue

                adjustment["GRN"] = invoice_details[0]["GRN No"]
                if "Order" in adj_type:
                    adjustment["ID"] = invoice_details[0]["Invoice No"]
                    adjustment["Type"] = "DPMC/Invoice"
            else:
                logging.error(
                        f'An error has occurred !!! \nStatus: {response.status_code} \nFor reason: {response.reason}')

    with open(ADJ_DPMC_FILE, "w") as invoice_file:
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
    with open(ADJ_DPMC_FILE, "r") as invoice_file:
        invoice_reader = json.load(invoice_file)
    adjustments = invoice_reader["Adjustments"]

    for adjustment in adjustments:
        adj_type = adjustment["Type"]

        if "DPMC" in adj_type:
            if "Missing" in adj_type:
                logging.warning("Invoice with missing identifiers are still present.")
                continue
            adj_ref = adjustment["ID"]
            grn_number = adjustment["GRN"] if "GRN" in adjustment else None
            adjustment["Products"] = []

            payload_mid = f"&strInvoiceNo={adj_ref}&" \
                          "strPADealerCode=AC2011063676&" \
                          "STR_FORM_ID=00605"
            payload = "strMode=GRN&" \
                      f"strGRNno={grn_number + payload_mid}&" \
                      "STR_FUNCTION_ID=IQ" \
                if grn_number else f"strMode=INVOICE{payload_mid}&" \
                                   "STR_FUNCTION_ID=CR"
            payload = f"{payload}&" \
                      "STR_PREMIS=KGL&" \
                      "STR_INSTANT=DLR&" \
                      "STR_APP_ID=00011"

            response = requests.request("POST", URL_PRODUCTS, headers = HEADERS, data = payload)

            if response:
                product_details = json.loads(response.text)["DATA"]

                if product_details == "NO DATA FOUND":
                    logging.warning(f"Invoice Number: {adjustment} is Invalid !!!")
                else:
                    product_details = product_details["dsGRNDetails"]["Table"] if "GRN" in adjustment \
                        else product_details["dtGRNDetails"]

                    for product_detail in product_details:
                        adjustment["Products"].append(product_detail)
            else:
                logging.error(
                        f'An error has occurred !!! \nStatus: {response.status_code} \nFor reason: {response.reason}')

    with open(ADJ_DPMC_FILE, "w") as invoice_file:
        json.dump(invoice_reader, invoice_file)
    logging.info("Product data scrapping done.")


def json_to_csv(file):
    # -*- coding: utf-8 -*-
    """ Before
    get_products_from_invoices() should be called before

    ''' After Call
    Part Numbers with the quantities will be in the `DATED_ADJUSTMENT_FILE`
    """
    with open(file, "r") as invoice_file:
        invoice_reader = json.load(invoice_file)
    adjustments = invoice_reader["Adjustments"]

    with open(DATED_ADJUSTMENT_FILE, "w") as adj_csv_file:
        field_names = ("name", "Product/Internal Reference", "Counted Quantity")
        adj_writer = csv.DictWriter(adj_csv_file, fieldnames = field_names, delimiter = ',', quotechar = '"',
                                    quoting = csv.QUOTE_MINIMAL)
        adj_writer.writeheader()

        for adjustment in adjustments:
            adj_ref = None
            for product in adjustment["Products"]:
                product_number = product["STR_PART_NO"] if "STR_PART_NO" in product else product["STR_PART_CODE"]
                product_count = product["INT_QUANTITY"] if "INT_QUANTITY" in product else product["INT_QUATITY"]

                if "Sales" in adjustment["Type"]:
                    adj_ref = f"Sales of {product['DATE']}" if product['DATE'] != "" else adj_ref
                else:
                    adj_ref = adjustment["ID"]

                adj_writer.writerow({"name": adj_ref,
                                     "Product/Internal Reference": product_number,
                                     "Counted Quantity": float(product_count)})
    logging.info("Product data modeling done.")


def merge_duplicates():
    # -*- coding: utf-8 -*-
    """
    Add the sum of the duplicate products
    """
    df = pd.read_csv(DATED_ADJUSTMENT_FILE)
    df["Counted Quantity"] = df.groupby(["name", "Product/Internal Reference"])["Counted Quantity"].transform('sum')
    df.drop_duplicates(["name", "Product/Internal Reference"], inplace = True, keep = "last")
    df.to_csv(DATED_ADJUSTMENT_FILE, index = False)
    logging.info("Adjustment's duplicate products have been merged")


def inventory_adjustment():
    # -*- coding: utf-8 -*-
    """ Before
    json_to_csv() should be called before to get the adjustment file

    After Call
    Final file to upload will be available at `DATED_ADJUSTMENT_FILE`
    """
    products = []
    qty_fixable_products = []
    invalid_products = []
    previous_adjustment_invoice = None

    with open(INVENTORY_FILE, "r") as inventory_file, open(DATED_ADJUSTMENT_FILE, "r") as adjustment_file:
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

        for inventory_product in inventory_reader:
            inventory_number = inventory_product["Internal Reference"]
            inventory_quantity = float(inventory_product["Quantity On Hand"])

            if adjustment_number == inventory_number:
                exists = True
                finalised_quantity = inventory_quantity + adjustment_quantity
                product_data = [adjustment_invoice, is_exhausted_included, inventory_number,
                                inventory_product["Product/Product/ID"], 'stock.stock_location_stock',
                                inventory_quantity, adjustment_quantity, finalised_quantity]

                if inventory_quantity < 0:
                    qty_fixable_products.append(product_data)
                    logging.warning(f"Inventory initial qty is negative: {adjustment_number}."
                                    f"Inventory: {inventory_quantity}. Difference: {adjustment_quantity} . Finalised "
                                    f"qty: {finalised_quantity}.")
                elif finalised_quantity < 0:
                    qty_fixable_products.append(product_data)
                    logging.warning(f"Inventory final qty is negative: {adjustment_number}."
                                    f"Inventory: {inventory_quantity}. Difference: {adjustment_quantity}. Finalised "
                                    f"qty: {finalised_quantity}.")

                products.append([adjustment_invoice, is_exhausted_included, inventory_number,
                                 inventory_product["Product/Product/ID"], 'stock.stock_location_stock',
                                 finalised_quantity])
                # Update `previous_adjustment_invoice` if `adjustment_invoice` is valid and exists
                previous_adjustment_invoice = adjustment_product["name"]
                break

        if not exists:
            invalid_products.append(adjustment_product)

    # Log products that are unavailable in the system
    for product in invalid_products:
        logging.error(f"Product Number: {product['Product/Internal Reference']} is Invalid !!!")

    # _create_quantity_fixes(qty_fixable_products)
    columns = ['name', 'Include Exhausted Products', 'reference', 'line_ids/product_id/id', 'line_ids/location_id/id',
               'line_ids/product_qty']
    df = pd.DataFrame(columns = columns, data = products)
    df.to_csv(DATED_ADJUSTMENT_FILE, encoding = 'utf-8', mode = 'w', header = True, index = False)

    logging.info("Inventory Adjustment done.")


def _create_quantity_fixes(products):
    """
    Create file for products with negative inventories
    """
    columns = ['name', 'Include Exhausted Products', 'reference', 'line_ids/product_id/id', 'line_ids/location_id/id',
               'initial_qty', 'difference', 'line_ids/product_qty']
    df = pd.DataFrame(columns = columns, data = products)
    df.to_csv(FIX_FILE, encoding = 'utf-8', mode = 'w', header = True, index = False)


def _format_sales_data(number):
    match = re.search(r"(?<=\[).+?(?=])", number)
    return match.group()


def read_sales_data():
    sales_df = pd.read_excel(SALES_PATH,
                             skiprows = list(range(4)),
                             header = None,
                             names = ['number', 'quantity'],
                             dtype = {'number': str},
                             converters = {'number': _format_sales_data})
    fixable_products_df = pd.read_csv(FIX_FILE,
                                      dtype = {'reference': str})
    sales_mask = sales_df.number.isin(fixable_products_df.reference)
    sales_df = sales_df[sales_mask]

    print()


def get_sales_adjustments():
    sheet.main()


def get_other_adjustments():
    json_to_csv(ADJ_OTHER_FILE)


def get_dpmc_adjustments():
    HEADERS["cookie"] = dpmc.authorise()
    logging.info(f"Session created. Cookie: {HEADERS['cookie']} \n"
                 f"==================================================================================================")
    get_grn_for_invoice()
    get_products_from_invoices()
    json_to_csv(ADJ_DPMC_FILE)


if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")
    get_other_adjustments()
    inventory_adjustment()
