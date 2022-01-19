from __future__ import print_function, unicode_literals
from datetime import date
from app.config import ROOT_DIR
import app.clients.dpmc_client as dpmc_client

import re
import csv
import json
import requests
import logging
import pandas as pd
import app.googlesheet as sheet

# -*- Dir Paths -*-
INV_DIR = f'{ROOT_DIR}/data/inventory'
SALES_DIR = f'{ROOT_DIR}/data/sales'
ADJ_DIR = f'{INV_DIR}/adjustments'
# -*- File Paths -*-
ADJ_DPMC_FILE = f'{INV_DIR}/adjustment.dpmc.json'
ADJ_OTHER_FILE = f'{INV_DIR}/adjustment.other.json'
INVENTORY_FILE = f'{INV_DIR}/product.inventory.csv'
SALES_FILE = f'{SALES_DIR}/sales.xlsx'
FIX_FILE = f'{ADJ_DIR}/{date.today()}-fix.csv'
DATED_ADJUSTMENT_FILE = f'{ADJ_DIR}/{date.today()}-adjustment-2.csv'

# -*- Request Paths -*-
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


def _fetch_grn_invoice():
    logging.info("GRN Invoice retrieval started")
    adjustments = pd.read_json(ADJ_DPMC_FILE, orient = "records").Adjustments.to_list()

    for adjustment in adjustments:
        adjustment_type = adjustment["Type"]
        adjustment_id = adjustment["ID"]
        if "Order" in adjustment_type:
            response_data = dpmc_client.get_grn_from_order(adjustment_id)
            column_name = "STR_ORDER_NO"
        else:
            response_data = dpmc_client.get_grn_from_mobile(adjustment_id)
            column_name = "STR_MOBILE_NO"
        if "NO DATA FOUND" in response_data:
            response_data = dpmc_client.get_grn_from_column(column_name, adjustment_id)
            if "NO DATA FOUND" in response_data:
                adjustment["Type"] = "Invalid"
                logging.warning(f"GRN not found for {adjustment_id}")
                continue
        response_data = json.loads(response_data)[0]
        adjustment["Type"] = "Invoice"
        adjustment["ID"] = response_data["Invoice No"]
        adjustment["GRN"] = response_data["GRN No"] if "GRN No" in response_data else None
        logging.info(f"GRN retrieved for {adjustment['ID']} of {adjustment['Type']}")

    adjustments = {"Adjustments": adjustments}
    with open(ADJ_DPMC_FILE, "w") as file:
        json.dump(adjustments, file)
    logging.info("GRN Invoice retrieval completed")


def _fetch_products():
    logging.info("Product retrieval started")
    adjustments = pd.read_json(ADJ_DPMC_FILE, orient = "records").Adjustments.to_list()

    for adjustment in adjustments:
        adjustment_type = adjustment["Type"]
        adjustment_id = adjustment["ID"]
        grn_number = adjustment["GRN"]
        if "Missing" in adjustment_type:
            logging.warning(f"Missing adjustment {adjustment_id}")
            continue
        response_data = dpmc_client.get_products(adjustment_id, grn_number)
        response_data = response_data["DATA"]
        if "NO DATA FOUND" in response_data:
            logging.warning(f"Products not found for {adjustment_id}")
            continue
        products = response_data["dsGRNDetails"]["Table"] if adjustment["GRN"] else response_data["dtGRNDetails"]
        adjustment["Products"] = products
        logging.info(f"Products retrieved for {adjustment_id}")

    adjustments = {"Adjustment": adjustments}
    with open(ADJ_DPMC_FILE, "w") as file:
        json.dump(adjustments, file)
    logging.info("Product retrieval completed")


def json_to_csv(file):
    adjustments = pd.read_json(file, orient = 'records').Adjustments.to_list()
    sorted_adjustment = pd \
        .json_normalize(adjustments) \
        .sort_values(by = ['Date', 'ID']) \
        .to_dict('records')

    with open(DATED_ADJUSTMENT_FILE, "w") as adj_csv_file:
        field_names = ("name", "Accounting Date", "Product/Internal Reference", "Counted Quantity")
        adj_writer = csv.DictWriter(adj_csv_file, fieldnames = field_names, delimiter = ',', quotechar = '"',
                                    quoting = csv.QUOTE_MINIMAL)
        adj_writer.writeheader()
        for adjustment in sorted_adjustment:
            for product in adjustment["Products"]:
                product_number = product["STR_PART_NO"] if "STR_PART_NO" in product else product["STR_PART_CODE"]
                product_count = product["INT_QUANTITY"] if "INT_QUANTITY" in product else product["INT_QUATITY"]

                adj_writer.writerow({"name": adjustment["ID"],
                                     "Accounting Date": adjustment["Date"],
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


def inventory_adjustment(dated_adj_file):
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

    with open(INVENTORY_FILE, "r") as inventory_file, open(dated_adj_file, "r") as adjustment_file:
        inventory_reader = list(csv.DictReader(inventory_file))
        adjustment_reader = list(csv.DictReader(adjustment_file))

    for adjustment_product in adjustment_reader:
        exists = False
        adjustment_invoice = adjustment_product["name"]
        accounting_date = adjustment_product["Accounting Date"]
        is_exhausted_included = True
        adjustment_number = adjustment_product["Product/Internal Reference"]
        adjustment_quantity = float(adjustment_product["Counted Quantity"])

        if adjustment_invoice == previous_adjustment_invoice:
            adjustment_invoice = None
            accounting_date = None
            is_exhausted_included = None

        for inventory_product in inventory_reader:
            inventory_number = inventory_product["Internal Reference"]
            inventory_quantity = float(inventory_product["Quantity On Hand"])
            regex = r"\((\w+)\)"
            match = re.search(regex, inventory_number)
            if match:
                split = re.split(regex, inventory_number)
                product_numbers = split[0].split(",")
                pos_category_name = split[1]
                inventory_number = [f"{product_number}({pos_category_name})" for product_number in product_numbers]

            if isinstance(inventory_number, list):
                if adjustment_number in inventory_number:
                    exists = True
            else:
                if adjustment_number == inventory_number:
                    exists = True

            if exists:
                finalised_quantity = inventory_quantity + adjustment_quantity
                product_data = [adjustment_invoice, is_exhausted_included, inventory_product["Internal Reference"],
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

                products.append([adjustment_invoice, accounting_date, is_exhausted_included,
                                 inventory_product["Internal Reference"], inventory_product["Product/Product/ID"],
                                 'stock.stock_location_stock', finalised_quantity])
                # Update `previous_adjustment_invoice` if `adjustment_invoice` is valid and exists
                previous_adjustment_invoice = adjustment_product["name"]
                break

        if not exists:
            invalid_products.append(adjustment_product)

    # Log products that are unavailable in the system
    for product in invalid_products:
        logging.error(f"Product Number: {product['Product/Internal Reference']} is Invalid !!!")

    # _create_quantity_fixes(qty_fixable_products)
    columns = ['name', 'Accounting Date', 'Include Exhausted Products', 'reference', 'line_ids/product_id/id',
               'line_ids/location_id/id', 'line_ids/product_qty']
    df = pd.DataFrame(columns = columns, data = products)
    df.to_csv(dated_adj_file, encoding = 'utf-8', mode = 'w', header = True, index = False)

    logging.info("Inventory Adjustment done.")
    return invalid_products


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
    sales_df = pd.read_excel(SALES_FILE)
    print()
    # sales_df = pd.read_excel(SALES_FILE,
    #                          skiprows = list(range(4)),
    #                          header = None,
    #                          names = ['number', 'quantity'],
    #                          dtype = {'number': str},
    #                          converters = {'number': _format_sales_data})
    # fixable_products_df = pd.read_csv(FIX_FILE,
    #                                   dtype = {'reference': str})
    # sales_mask = sales_df.number.isin(fixable_products_df.reference)
    # sales_df = sales_df[sales_mask]
    # print()


def get_sales_adjustments():
    # sheet.main()
    # merge_duplicates()
    inventory_adjustment(DATED_ADJUSTMENT_FILE)


def get_other_adjustments():
    json_to_csv(ADJ_OTHER_FILE)
    inventory_adjustment(DATED_ADJUSTMENT_FILE)


def get_dpmc_adjustments():
    HEADERS["cookie"] = dpmc_client.authenticate()
    logging.info(f"Session created. Cookie: {HEADERS['cookie']}")
    # _fetch_grn_invoice()
    _fetch_products()
    # get_products_from_invoices()
    # json_to_csv(ADJ_DPMC_FILE)
    # inventory_adjustment(DATED_ADJUSTMENT_FILE)


if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")
    get_dpmc_adjustments()
