from __future__ import print_function, unicode_literals
from app.config import ROOT_DIR
from app.bots.InventoryBot import ADJ_DIR, inventory_adjustment
from datetime import date

import sys
import re
import logging
import pandas as pd

PRODUCT_FILE = f"{ROOT_DIR}/data/product/product.product.csv"
POS_CATEGORY_FILE = f"{ROOT_DIR}/data/product/pos.category.csv"
INVENTORY_FILE = f"{ROOT_DIR}/data/inventory/product.inventory.csv"
ADJUSTMENT_FILE = f"{ROOT_DIR}/data/inventory/adjustment.other.txt"


def create_adj_file():
    all_capitals = ["4s", "5p", "ct", "cdi", "dh", "dz", "jk", "lh", "nd", "nm", "ns", "rh", "ug"]
    adj_name = f"Nishan Automobile Invoice - {invoice_number}"

    with open(ADJUSTMENT_FILE) as file:
        lines = file.readlines()

    products = []
    for line in lines:
        words = line.split(" ")

        product = {
            "Name": adj_name,
            "Date": adj_date,
            "PartName": " ".join(words[1:-4]).title(),
            "PartNumber": words[-4],
            "Quantity": words[-3],
            "Price": words[-2].replace(",", ""),
            }
        products.append(product)
    products_df = pd.DataFrame(products)
    products_df.to_csv(dated_adj_file, index = False,
                       header = ["name", "Accounting Date", "PartName", "Product/Internal Reference",
                                 "Counted Quantity", "Price"])


def create_product_file(products):
    product_df = pd.DataFrame(products)
    print(product_df.to_markdown())

    product_df = product_df \
        .drop(["name", "Counted Quantity"], axis = 1) \
        .rename(columns = {"PartName": "Name",
                           "Product/Internal Reference": "Internal Reference",
                           "Price": "Sales Price"})
    product_df = product_df.assign(**{"Product Category/ID": "product.product_category_1",
                                      "Product Type": "Storable Product",
                                      "Cost": product_df["Sales Price"],
                                      "Customer Taxes": "",
                                      "Available in POS": True,
                                      "Can be Purchased": True,
                                      "Can be Sold": True})
    product_df = product_df.apply(_get_product_category, axis = 1)
    product_df["Description"] = product_df["Name"]

    columns = ["Internal Reference",
               "Name",
               "Description",
               "Product Category/ID",
               "Point of Sale Category/ID",
               "Product Type",
               "Cost",
               "Sales Price",
               "Customer Taxes",
               "Available in POS",
               "Can be Purchased",
               "Can be Sold",
               "Image"]
    product_df.to_csv(PRODUCT_FILE, index = False, columns = columns)


def _get_product_category(product_df):
    pos_category_df = pd.read_csv(POS_CATEGORY_FILE)
    part_number = product_df["Internal Reference"]

    m = re.search(r"\((\w+)\)", part_number)
    if m:
        pos_category = m.group(1)
        if pos_category in pos_category_df.Code.values:
            product_df["Name"] = f"{pos_category} {product_df['Name']}"
            pos_category = pos_category_df.loc[pos_category_df["Code"] == pos_category]
            product_df["Point of Sale Category/ID"] = pos_category.ID.values[0]
            product_df["Image"] = pos_category.Image.values[0]
            return product_df
        else:
            print(f"Invalid POS category {pos_category} received.")
            sys.exit(0)
    # Product is an original bajaj Bajaj
    print(f"Using default POS category for {part_number}.")
    product_df["Point of Sale Category/ID"] = \
        pos_category_df.loc[pos_category_df["Display Name"] == "Bajaj"].ID.values[0]
    return product_df


if __name__ == "__main__":
    # logging config
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")
    # basic config
    invoice_number = "SKL0006920"
    adj_date = "2022-02-14"
    dated_adj_file = f"{ADJ_DIR}/{date.today()}-nishan-adjustment.csv"
    # function calls
    create_adj_file()
    invalid_products = inventory_adjustment(dated_adj_file)
    if invalid_products:
        create_product_file(invalid_products)
