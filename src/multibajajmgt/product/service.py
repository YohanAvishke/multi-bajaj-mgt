import re
import sys

import pandas as pd
import multibajajmgt.client.odoo.client as odoo_client

from loguru import logger as log
from multibajajmgt.common import *
from multibajajmgt.config import (
    INVOICE_HISTORY_DIR, PRICE_HISTORY_DIR, PRODUCT_HISTORY_DIR, PRODUCT_TMPL_DIR, STOCK_ALL_FILE
)
from multibajajmgt.enums import (
    BasicFieldName as Basic,
    DocumentResourceExtension as DRExt,
    DocumentResourceName as DRName,
    InvoiceField as InvoField,
    InvoiceStatus as Status,
    OdooFieldLabel as OdooLabel,
)
from multibajajmgt.product.models import Product

curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_price_dir = get_dated_dir(PRICE_HISTORY_DIR)
curr_prod_dir = get_dated_dir(PRODUCT_HISTORY_DIR)


def create_products():
    stock_df = pd.read_csv(STOCK_ALL_FILE)
    pos_categories_df = pd.read_csv(f"{PRODUCT_TMPL_DIR}/pos.category.csv")
    prod_categ_df = pd.read_csv(f"{PRODUCT_TMPL_DIR}/product.category.csv")
    invoices_df = pd.read_json(f"{curr_invoice_dir}/{DRName.invoice_tp}.{DRExt.json}", convert_dates = False)
    invoices_df = invoices_df[invoices_df[Basic.status] == Status.success]
    for invo_row in invoices_df.itertuples():
        products_df = pd.json_normalize(invo_row.Products)
        # Find missing products
        products_df = products_df.merge(stock_df, how = "left", indicator = Basic.found_in,
                                        left_on = InvoField.part_code, right_on = OdooLabel.internal_id)
        products_df = products_df[products_df[Basic.found_in] == "left_only"]
        # No missing products
        if len(products_df) == 0:
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
                    pos_categ_data = pos_categ_df.iloc[0]
                    # Gather data to create the product
                    pos_categ_name = pos_categ_data["Display Name"].split(" / ")[-1]
                    pos_categ_id = odoo_client.fetch_pos_category(pos_categ_name)[0]["id"]
                    image_code = pos_categ_data["Image"]
                    # TODO Yellow Label's should fetch data from DPMC client
                    name = f"{pos_code} {prod_row.Name}"
                    price = prod_row[4]
                    product = Product(name, internal_ref, price = price, image = image_code, categ_id = 1,
                                      pos_categ_id = pos_categ_id)
                    odoo_client.create_product(product)
                else:
                    log.warning(f"Invalid POS category {pos_code} for {internal_ref}")
                    continue
            else:
                # Original Bajaj product
                # Todo call bajaj prod creation after impl
                log.warning(f"Found original Bajaj product for {internal_ref}")
                continue
