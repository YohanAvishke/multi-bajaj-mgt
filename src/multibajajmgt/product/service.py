import sys

import multibajajmgt.client.odoo.client as odoo_client
import pandas as pd
import time
import re

from loguru import logger as log
from multibajajmgt.common import get_dated_dir, write_to_csv
from multibajajmgt.config import (
    INVOICE_HISTORY_DIR, PRICE_HISTORY_DIR, PRODUCT_HISTORY_FILE, PRODUCT_TMPL_DIR, STOCK_ALL_FILE
)
from multibajajmgt.enums import (
    BasicFieldName as Basic,
    DocumentResourceExtension as DRExt,
    DocumentResourceName as DRName,
    InvoiceField as InvoField,
    InvoiceStatus as Status,
    OdooFieldLabel as OdooLabel,
)
from multibajajmgt.exceptions import InvalidDataFormatReceived, ProductCreationFailed
from multibajajmgt.product.models import Product

cur_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_price_dir = get_dated_dir(PRICE_HISTORY_DIR)


def _save_historical_data(product_ids):
    """ Store products that are just created with their creation date

    :param product_ids: list, created products
    """
    products_his_df = pd.read_csv(PRODUCT_HISTORY_FILE)
    # Add newly created products to history
    product_ids_df = pd.DataFrame(product_ids)
    products_his_df = pd.concat([products_his_df, product_ids_df])
    write_to_csv(PRODUCT_HISTORY_FILE, products_his_df)


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
        image_code = pos_categ_data["Image"]
        # TODO Yellow Label's should fetch data from DPMC client
        name = f"{pos_code} {prod_row.Name}"
        price = prod_row[4]
        product = Product(name, prod_row.ID, price = price, image = image_code, categ_id = 1,
                          pos_categ_id = pos_categ_id)
        return product


def _compare_invo_stock_prods(invo_row):
    """ Identify non-existing products in the odoo stock

    :param invo_row: itertuple row, invoice with product data
    :return: pandas dataframe, non-existing products
    """
    stock_df = pd.read_csv(STOCK_ALL_FILE)
    df = pd.json_normalize(invo_row.Products)
    # noinspection PyTypeChecker
    df = df.merge(stock_df, how = "left", indicator = Basic.found_in,
                  left_on = InvoField.part_code, right_on = OdooLabel.internal_id)
    df = df[df[Basic.found_in] == "left_only"]
    return df


def create_missing_products():
    """ Create records for invalid products from third-party invoices
    """
    log.info("Creating unavailable products in the invoice")
    created_product_ids = []
    pos_categories_df = pd.read_csv(f"{PRODUCT_TMPL_DIR}/pos.category.csv")
    invoices_df = pd.read_json(f"{curr_invoice_dir}/{DRName.invoice_tp}.{DRExt.json}", convert_dates = False)
    invoices_df = invoices_df[invoices_df[Basic.status] == Status.success]
    for invo_row in invoices_df.itertuples():
        # Filter missing products
        products_df = _compare_invo_stock_prods(invo_row)
        if len(products_df) == 0:
            # No missing products
            continue
        for prod_row in products_df.itertuples():
            # Extract pos categ from product
            internal_ref = prod_row.ID
            find = re.search(r"\((\w+)\)", internal_ref)
            if find:
                # Third-party product
                pos_code = find.group(1)
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
            else:
                # Original Bajaj product
                # Todo call bajaj prod creation after impl
                log.warning(f"Found original Bajaj product for {internal_ref}")
                continue
    _save_historical_data(created_product_ids)
