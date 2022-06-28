from app.config import ROOT_DIR

import sys
import re
import logging
import pandas as pd

# configurations
logging_format = "%(asctime)s: %(levelname)s - %(message)s"
logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")
# file paths
INVOICE_FILE_PATH = f"{ROOT_DIR}/data/inventory/adjustment.other.txt"
INVENTORY_FILE_PATH = f"{ROOT_DIR}/data/inventory/product.inventory.csv"
POS_CATEGORY_FILE_PATH = f"{ROOT_DIR}/data/product/pos.category.csv"
PRODUCT_FILE_PATH = f"{ROOT_DIR}/data/product/product.product.csv"
PRICE_FILE_PATH = f"{ROOT_DIR}/data/product/product.price.csv"

invoice_name = ""
invoice_number = ""
date = ""


def _enrich_invoice(invoice_row):
    raw_data = invoice_row["InvoiceName"]
    global invoice_name
    global invoice_number
    global date
    invoice_data = []

    if raw_data[0] == "*":
        invoice_data = raw_data.split("*")[-1].split("&")
    if invoice_data:
        invoice_name = invoice_data[0]
        invoice_number = invoice_data[1]
        date = invoice_data[2]
    else:
        raw_data = raw_data.split(" ")
        invoice_row.ProductName = str(" ".join(raw_data[0:-3]).title())
        invoice_row.ProductNumber = str(raw_data[-3])
        invoice_row.Quantity = int(raw_data[-2])
        invoice_row.Price = float(raw_data[-1].replace(",", ""))
    invoice_row.InvoiceName = str(invoice_name)
    invoice_row.InvoiceNumber = str(invoice_number)
    invoice_row.Date = date

    return invoice_row


def _update_statuses(invoice_row, inventory_df):
    if not pd.isna(invoice_row["ProductNumber"]):
        inventory_row = inventory_df[inventory_df["Internal Reference"] == invoice_row["ProductNumber"]]
        if not inventory_row.empty:
            invoice_row["Exists"] = True
            invoice_row["ExternalId"] = inventory_row.iloc[0]["ID"]
            invoice_row["OutdatedSalesPrice"] = inventory_row.iloc[0]["Sales Price"]
            invoice_row["OutdatedCost"] = inventory_row.iloc[0]["Cost"]
            if (inventory_row["Sales Price"] < invoice_row["Price"]).iloc[0]:
                invoice_row["PriceStatus"] = "up"
            elif (inventory_row["Sales Price"] > invoice_row["Price"]).iloc[0]:
                invoice_row["PriceStatus"] = "down"
            else:
                invoice_row["PriceStatus"] = "equal"
        else:
            invoice_row["Exists"] = False
    return invoice_row


def _add_pos_category(product_row):
    pos_category_df = pd.read_csv(POS_CATEGORY_FILE_PATH)
    part_number = product_row["Internal Reference"]

    m = re.search(r"\((\w+)\)", part_number)
    if m:
        pos_category = m.group(1)
        if pos_category in pos_category_df.Code.values:
            product_row["Name"] = f"{pos_category} {product_row['Name']}"
            pos_category = pos_category_df.loc[pos_category_df["Code"] == pos_category]
            product_row["Point of Sale Category/ID"] = pos_category.ID.values[0]
            product_row["Image"] = pos_category.Image.values[0]
            return product_row
        else:
            print(f"Invalid POS category {pos_category} received.")
            sys.exit(0)
    # Product is an original bajaj Bajaj
    print(f"Using default POS category for {part_number}.")
    product_row["Point of Sale Category/ID"] = \
        pos_category_df.loc[pos_category_df["Display Name"] == "Bajaj"].ID.values[0]
    return product_row


def create_product_creation(product_df):
    product_df = product_df \
        .rename(columns = {"ProductName": "Name", "ProductNumber": "Internal Reference",
                           "Price": "Sales Price"})
    product_df = product_df.assign(**{"Product Category/ID": "product.product_category_1",
                                      "Product Type": "Storable Product",
                                      "Cost": product_df["Sales Price"],
                                      "Customer Taxes": "",
                                      "Available in POS": True,
                                      "Can be Purchased": True,
                                      "Can be Sold": True})
    product_df = product_df.apply(_add_pos_category, axis = 1)
    product_df["Description"] = product_df["Name"]
    if not product_df.empty:
        product_df.to_csv(PRODUCT_FILE_PATH, index = False,
                          columns = ["Internal Reference", "Name", "Description", "Product Category/ID",
                                     "Point of Sale Category/ID", "Product Type", "Cost", "Sales Price",
                                     "Customer Taxes", "Available in POS", "Can be Purchased", "Can be Sold", "Image"])


def create_price_update(product_df):
    product_df = product_df \
        .rename(columns = {"ExternalId": "ID", "ProductNumber": "Internal Reference", "Price": "Sales Price"})
    product_df["Cost"] = product_df["Sales Price"]
    if not product_df.empty:
        product_df.to_csv(PRICE_FILE_PATH, index = False,
                          columns = ["ID", "Internal Reference", "Sales Price", "Cost", "OutdatedSalesPrice",
                                     "OutdatedCost"])


def main():
    invoice_df = pd.read_csv(INVOICE_FILE_PATH, delimiter = "\t", header = None,
                             names = ["InvoiceName", "InvoiceNumber", 'Date', "ProductName", "ProductNumber",
                                      "Quantity", "Price"])
    invoice_df = invoice_df.apply(_enrich_invoice, axis = 1)

    invoice_df["Quantity"] = invoice_df.groupby(["InvoiceNumber", "ProductNumber"])["Quantity"].transform("sum")
    invoice_df.drop_duplicates(["InvoiceNumber", "ProductNumber"], inplace = True, keep = "last")

    inventory_df = pd.read_csv(INVENTORY_FILE_PATH)
    invoice_df = invoice_df.apply(_update_statuses, axis = 1, inventory_df = inventory_df)

    new_product_df = invoice_df[invoice_df["Exists"] == False]
    create_product_creation(new_product_df)

    outdated_price_df = invoice_df[(invoice_df["PriceStatus"] == "up") | (invoice_df["PriceStatus"] == "down")]
    create_price_update(outdated_price_df)


if __name__ == "__main__":
    main()
    # TODO
    #
