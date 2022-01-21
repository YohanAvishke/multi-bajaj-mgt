from __future__ import print_function, unicode_literals
from datetime import date
from app.config import ROOT_DIR

import re
import csv
import json
import logging
import pandas as pd
import app.clients.dpmc_client as dpmc_client
import app.clients.googlesheet.client as sheet_client

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
DATED_ADJUSTMENT_FILE = f'{ADJ_DIR}/{date.today()}-adjustment.csv'


def _fetch_grn_invoice():
    logging.info("GRN Invoice retrieval started")
    adjustments = pd.read_json(ADJ_DPMC_FILE, orient = "records").Adjustments.to_list()

    for adjustment in adjustments:
        adjustment_type = adjustment["Type"]
        adjustment_id = adjustment["ID"]

        if "Invoice" in adjustment_type:
            column_name = "STR_INVOICE_NO"
            response_data = dpmc_client.get_grn_from_column(column_name, adjustment_id)
        elif "Order" in adjustment_type:
            column_name = "STR_ORDER_NO"
            response_data = dpmc_client.get_grn_from_column(column_name, adjustment_id)
        else:
            column_name = "STR_MOBILE_NO"
            response_data = dpmc_client.get_grn_from_mobile(adjustment_id)

        if "NO DATA FOUND" in response_data:
            response_data = dpmc_client.get_grn_from_column(column_name, adjustment_id)
            if "NO DATA FOUND" in response_data:
                adjustment["GRN"] = None
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

    adjustments = {"Adjustments": adjustments}
    with open(ADJ_DPMC_FILE, "w") as file:
        json.dump(adjustments, file)
    logging.info("Product retrieval completed")


def _save_dated_adjustment(file):
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
    df = pd.read_csv(DATED_ADJUSTMENT_FILE)
    df["Counted Quantity"] = df.groupby(["name", "Product/Internal Reference"])["Counted Quantity"].transform('sum')
    df.drop_duplicates(["name", "Product/Internal Reference"], inplace = True, keep = "last")
    df.to_csv(DATED_ADJUSTMENT_FILE, index = False)
    logging.info("Adjustment's duplicate products have been merged")


def inventory_adjustment(dated_adj_file):
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

    columns = ['name', 'Accounting Date', 'Include Exhausted Products', 'reference', 'line_ids/product_id/id',
               'line_ids/location_id/id', 'line_ids/product_qty']
    df = pd.DataFrame(columns = columns, data = products)
    df.to_csv(dated_adj_file, encoding = 'utf-8', mode = 'w', header = True, index = False)

    logging.info("Inventory Adjustment done.")
    return invalid_products


def get_sales_adjustments():
    sheet_client.main()
    inventory_adjustment(DATED_ADJUSTMENT_FILE)


def get_other_adjustments():
    _save_dated_adjustment(ADJ_OTHER_FILE)
    inventory_adjustment(DATED_ADJUSTMENT_FILE)


def get_dpmc_adjustments():
    # dpmc_client.authenticate()
    # _fetch_grn_invoice()
    # _fetch_products()
    # _save_dated_adjustment(ADJ_DPMC_FILE)
    inventory_adjustment(DATED_ADJUSTMENT_FILE)


if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")
    get_dpmc_adjustments()
