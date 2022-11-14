import re
import sys
import time

import multibajajmgt.client.dpmc.client as dpmc_client
import multibajajmgt.client.odoo.client as odoo_client
import pandas as pd

from loguru import logger as log
from multibajajmgt.common import get_dated_dir, get_files, write_to_csv
from multibajajmgt.config import INVOICE_HISTORY_DIR, PRICE_HISTORY_DIR, PRODUCT_DIR, PRODUCT_TMPL_DIR, STOCK_DIR
from multibajajmgt.enums import (
    BasicFieldName as Basic,
    DocumentResourceExtension as DocExt,
    DocumentResourceName as DocName,
    InvoiceField as InvoField,
    InvoiceStatus as Status,
    OdooFieldLabel as OdooLabel,
)
from multibajajmgt.exceptions import InvalidDataFormatReceived, InvalidIdentityError, ProductCreationFailed
from multibajajmgt.product.models import Product

cur_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_price_dir = get_dated_dir(PRICE_HISTORY_DIR)


def _save_historical_data(product_ids):
    """ Store products that are just created with their creation date

    :param product_ids: list, created products
    """
    product_history_file = f"{DocName.product_history}.{DocExt.csv}"
    products_his_df = pd.read_csv(f"{PRODUCT_DIR}/{product_history_file}")
    # Add newly created products to history
    product_ids_df = pd.DataFrame(product_ids)
    products_his_df = pd.concat([products_his_df, product_ids_df])
    write_to_csv(f"{PRODUCT_DIR}/{product_history_file}", products_his_df)


def _fetch_dpmc_product_data(id):
    try:
        category = dpmc_client.inquire_product_category(id)
        product = dpmc_client.inquire_product(id)
    except InvalidIdentityError as e:
        log.warning("Fetching dpmc product: {} failed with: {}", id, e.args)
        return



def _form_product_obj(prod_row, pos_code, pos_categ_df):
    """ Fetch and create a product object to be created in Odoo server

    :param prod_row: itertuple row, basic product data
    :param pos_code: string, code to identify pos category
    :param pos_categ_df: pandas dataframe, advanced category information
    :return: Product, creatable product
    """
    pos_categ_data = pos_categ_df.iloc[0]
    # Gather data to create the product
    pos_categ_name = pos_categ_data["Display Name"].split(" / ")[-1]
    try:
        pos_categ_id = odoo_client.fetch_pos_category(pos_categ_name)[0]["id"]
    except InvalidDataFormatReceived as e:
        raise ProductCreationFailed("Failed to retrieve POS category", e)
    else:
        if pos_code == "BAJAJ" or pos_code == "YL":
            _fetch_dpmc_product_data(prod_row.ID)
        else:
            name = f"{pos_code} {prod_row.Name}"

        image_code = pos_categ_data["Image"]
        price = prod_row[4]
        product = Product(name, prod_row.ID, price = price, image = image_code, categ_id = 1,
                          pos_categ_id = pos_categ_id)
        return product


def _form_dpmc_product_obj(prod_data, pos_code, pos_categ_df):
    return


def _find_invalid_products(invo_row):
    """ Identify non-existing products in the odoo stock

    :param invo_row: itertuple row, invoice with product data
    :return: pandas dataframe, non-existing products
    """
    stock_df = pd.read_csv(f"{STOCK_DIR}/{get_files().get_stock()}.{DocExt.csv}")
    df = pd.json_normalize(invo_row.Products)
    # noinspection PyTypeChecker
    df = df.merge(stock_df, how = "left", indicator = Basic.found_in,
                  left_on = InvoField.part_code, right_on = OdooLabel.internal_id)
    df = df[df[Basic.found_in] == "left_only"]
    return df


def create_missing_products():
    """ Create records for invalid products from third-party invoices
    """
    log.info("Creating invalid products from the invoice")
    created_product_ids = []
    pos_categories_df = pd.read_csv(f"{PRODUCT_TMPL_DIR}/pos.category.csv")
    invoices_df = pd.read_json(f"{curr_invoice_dir}/{get_files().get_invoice}.{DocExt.json}", convert_dates = False)
    invoices_df = invoices_df[invoices_df[Basic.status] == Status.success]
    for invo_row in invoices_df.itertuples():
        # Filter missing products
        invalids_df = _find_invalid_products(invo_row)
        if len(invalids_df) == 0:
            # No missing products
            continue
        for prod_row in invalids_df.itertuples():
            # Extract pos categ from product
            internal_ref = prod_row.ID
            find = re.search(r"\((\w+)\)", internal_ref)
            #  if: Third-party else: Bajaj product
            pos_code = find.group(1) if find else "BAJAJ"
            pos_categ_df = pos_categories_df.loc[pos_categories_df["Code"] == pos_code]
            if len(pos_categ_df) != 0:
                # Create product from the category and product data
                try:
                    product = _form_product_obj(prod_row, pos_code, pos_categ_df)
                except ProductCreationFailed as e:
                    log.error("Product creation failed {}", e)
                    _save_historical_data(created_product_ids)
                    sys.exit(0)
                else:
                    # Upload product
                    odoo_client.create_product(product)
                    created_product_ids.append({"Date": cur_date, "Internal Reference": internal_ref})
            else:
                log.warning(f"Invalid POS category {pos_code} for {internal_ref}")
                continue
    _save_historical_data(created_product_ids)


def update_barcode_nomenclature():
    """ Update DPMC products barcodes.
    """
    log.info("Creating a new barcode nomenclature")
    stock_df = pd.read_csv(f"{STOCK_DIR}/{get_files().get_stock()}.{DocExt.csv}")
    barcode_df = stock_df.drop(["Product/Product/ID", "Quantity_On_Hand"], axis = 1)
    barcode_df.at[0, "Barcode Nomenclature"] = f"DPMC Nomenclature {cur_date}"
    barcode_df = barcode_df.assign(**{"Rules/Rule Name": barcode_df["Internal Reference"],
                                      "Rules/Type": "Alias",
                                      "Rules/Alias": barcode_df["Internal Reference"],
                                      "Rules/Barcode Pattern": barcode_df["Internal Reference"] + "-{N}",
                                      "Rules/Sequence": "1"})
    barcode_df.drop(["Internal Reference"], axis = 1, inplace = True)
    barcode_df.loc[len(barcode_df)] = ["", "All Products", "Unit Product", "0", ".*", "2"]
    write_to_csv(f"{PRODUCT_DIR}/{DocName.product_barcode}.{DocExt.csv}", barcode_df,
                 header = ["Barcode Nomenclature", "Rules/Rule Name", "Rules/Type", "Rules/Alias",
                           "Rules/Barcode Pattern", "Rules/Sequence"])
