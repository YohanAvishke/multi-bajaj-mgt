from __future__ import print_function, unicode_literals
from app.config import ROOT_DIR
from app.bots.InventoryBot import ADJ_DIR, inventory_adjustment
from datetime import date

import sys
import re
import pandas as pd

INVOICE_NISHAN_FILE = f"{ROOT_DIR}/data/invoice/vendors/nishan.txt"
PRODUCT_FILE = f"{ROOT_DIR}/data/product/product.product.csv"
POS_CATEGORY_FILE = f"{ROOT_DIR}/data/product/pos.category.csv"

ADJ_SOURCES = {"nishan": "Nishan Automobile Invoice", "dilma": "Dilma Auto Trading Invoice"}


def create_adj_file():
    all_capitals = ["4s", "5p", "ct", "cdi", "dh", "dz", "jk", "lh", "nd", "nm", "ns", "rh", "ug"]
    adj_name = f"{ADJ_SOURCES[current_source]} - {invoice_number}"

    with open(INVOICE_NISHAN_FILE) as file:
        lines = file.readlines()

    products = []
    for line in lines:
        words = line.split(" ")

        product = {
            "Name": adj_name,
            "PartName": " ".join(words[1:-4]).title(),
            "PartNumber": words[-4],
            "Quantity": words[-3],
            "Price": words[-2].replace(",", ""),
            }
        products.append(product)
    products_df = pd.DataFrame(products)
    products_df.to_csv(dated_adj_file, index = False, header = ["name", "PartName", "Product/Internal Reference",
                                                                "Counted Quantity", "Price", "Total"])


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
            return product_df
        else:
            print(f"Invalid POS category {pos_category} received.")
            sys.exit(0)
    # Product is an original bajaj Bajaj
    print(f"Using default POS category for {part_number}.")
    product_df["Point of Sale Category/ID"] = \
        pos_category_df.loc[pos_category_df["Display Name"] == "Bajaj"].ID.values[0]
    return product_df


def create_product_file(products):
    product_df = pd.DataFrame(products)
    print(product_df.to_markdown())

    product_df = product_df.drop(["name",
                                  "Counted Quantity",
                                  "Total"],
                                 axis = 1).rename(columns = {"PartName": "Name",
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
               "Can be Sold"]
    product_df.to_csv(PRODUCT_FILE, index = False, columns = columns)


if __name__ == "__main__":
    invoice_number = "CB2003375"
    adj_date = "2021-12-24"
    current_source = "nishan"
    dated_adj_file = f"{ADJ_DIR}/{date.today()}-{current_source}-adjustment.csv"

    create_adj_file()
    invalid_products = inventory_adjustment(dated_adj_file)
    if invalid_products:
        create_product_file(invalid_products)
