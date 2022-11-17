import re
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
from multibajajmgt.exceptions import (InvalidDataFormatReceived, InvalidIdentityError, ProductInitException,
                                      ProductInquiryException)
from multibajajmgt.product.models import Product

cur_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_price_dir = get_dated_dir(PRICE_HISTORY_DIR)


def _save_historical_data(product_ids):
    """ Keep a list of products that are created.

    Store Creation Date and Internal Reference in a csv file.

    :param product_ids: list, created products.
    """
    product_history_file = f"{DocName.product_history}.{DocExt.csv}"
    products_his_df = pd.read_csv(f"{PRODUCT_DIR}/{product_history_file}")
    # Add newly created products to history
    product_ids_df = pd.DataFrame(product_ids)
    products_his_df = pd.concat([products_his_df, product_ids_df])
    write_to_csv(f"{PRODUCT_DIR}/{product_history_file}", products_his_df)


def _fetch_dpmc_product_data(ref_id):
    """ Fetch product's category and line information.

    :param ref_id: str, product's id.
    :return: dict, category + line data.
    """
    try:
        category = dpmc_client.inquire_product_category(ref_id)
        line = dpmc_client.inquire_product_line(ref_id)
        return category | line
    except InvalidIdentityError as e:
        raise ProductInquiryException(f"Failed to fetch category and line of: {ref_id}", e)


def _form_product_obj(prod_row, pos_code, pos_categ_df):
    """ Fetch and create a product object to be created in the Odoo server.

    :param prod_row: itertuple row, basic product data.
    :param pos_code: str, code to identify pos category.
    :param pos_categ_df: pandas dataframe, advanced category information.
    :return: Product, creatable product.
    """
    pos_categ_data = pos_categ_df.iloc[0]
    barcode = False
    if pos_code == "BAJAJ" or pos_code == "YL":
        ref_id = prod_row.ID.strip("(YL)")
        # Get DPMC product name, POS category and product category
        try:
            data = _fetch_dpmc_product_data(ref_id)
        except ProductInquiryException as e:
            raise ProductInitException(f"Data not found for {ref_id}.", e)
        # Figure pos code using vehicle code
        vehicle_code = data["STR_VEHICLE_TYPE_CODE"]
        if vehicle_code == "001":
            pos_categ_name = "2W"
        elif vehicle_code == "003":
            pos_categ_name = "3W"
        elif vehicle_code == "065":
            pos_categ_name = "QUTE"
        else:
            log.warning("Invalid vehicle code for: {}. Using default POS category.\n"
                        "Vehicle data: {} - {}.", ref_id, vehicle_code, data["STR_VEHICLE_TYPE"])
            pos_categ_name = "Bajaj"
        # Figure product name
        name = data["STR_DESC"].title()
        if pos_code == "YL":
            name = f"{pos_code} {name}"
        else:
            barcode = ref_id
    else:
        name = f"{pos_code} {prod_row.Name}"
        pos_categ_name = pos_categ_data["Display Name"].split(" / ")[-1]
    try:
        # Get Odoo POS category data
        pos_categ_id = odoo_client.fetch_pos_category(pos_categ_name)[0]["id"]
    except InvalidDataFormatReceived as e:
        raise ProductInitException(f"Failed fetching POS category: {pos_categ_name}.", e)
    # Create product obj
    image_code = pos_categ_data["Image"]
    price = prod_row[4]
    product = Product(name, prod_row.ID, barcode = barcode, price = price, image = image_code, categ_id = 1,
                      pos_categ_id = pos_categ_id)
    return product


def _find_invalid_products(invo_row):
    """ Identify non-existing products in the odoo stock.

    :param invo_row: itertuple row, invoice with product data.
    :return: pandas dataframe, non-existing products.
    """
    stock_df = pd.read_csv(f"{STOCK_DIR}/{get_files().get_stock()}.{DocExt.csv}")
    df = pd.json_normalize(invo_row.Products)
    # noinspection PyTypeChecker
    df = df.merge(stock_df, how = "left", indicator = Basic.found_in,
                  left_on = InvoField.part_code, right_on = OdooLabel.internal_id)
    df = df[df[Basic.found_in] == "left_only"]
    return df


def create_missing_products():
    """ Create records for invalid products from third-party invoices.
    """
    log.info("Create missing products of an invoice.")
    created_product_ids = []
    pos_categories_df = pd.read_csv(f"{PRODUCT_TMPL_DIR}/pos.category.csv")
    invoices_df = pd.read_json(f"{curr_invoice_dir}/{get_files().get_invoice()}.{DocExt.json}", convert_dates = False)
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
                except ProductInitException as e:
                    log.warning("Failed to initialize product object: {}, due to: {}.", internal_ref, e)
                    continue
                else:
                    # Upload product
                    odoo_client.create_product(product)
                    created_product_ids.append({"Date": cur_date, "Internal Reference": internal_ref})
            else:
                log.warning("Failed to create product: {}, due to invalid: {} POS category.", internal_ref, pos_code)
                continue
    _save_historical_data(created_product_ids)


def update_barcode_nomenclature():
    """ Update DPMC products barcodes.
    """
    log.info("Creating a new barcode nomenclature.")
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
