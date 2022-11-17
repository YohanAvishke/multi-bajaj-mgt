import itertools

import pandas as pd
import multibajajmgt.client.odoo.client as odoo_client

from loguru import logger as log
from multibajajmgt.common import csvstr_to_df, get_dated_dir, get_files, mk_dir, write_to_csv
from multibajajmgt.config import INVOICE_HISTORY_DIR, PRICE_DIR, PRICE_HISTORY_DIR
from multibajajmgt.enums import (
    BasicFieldName as Basic,
    DocumentResourceExtension as DocExt,
    InvoiceStatus as InvoStatus,
    InvoiceField as InvoField,
    OdooFieldLabel as OdooLabel,
    ProductPriceStatus as PriceStatus
)

curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_his_dir = get_dated_dir(PRICE_HISTORY_DIR)


def export_prices():
    """ Fetch and Save all(qty >= 0 and qty < 0) non DPMC product prices.
    """
    log.info("Export Third-Party prices.")
    raw_price = odoo_client.fetch_all_thirdparty_prices()
    price_df = csvstr_to_df(raw_price)
    write_to_csv(f"{PRICE_DIR}/{get_files().get_price()}.{DocExt.csv}", price_df)


def _extract_invoice_products():
    """ Combine all products of each successful invoice.

    :return: pandas dataframe, all products.
    """
    invoices_df = pd.read_json(f"{curr_invoice_dir}/{get_files().get_invoice()}.{DocExt.json}", convert_dates = False)
    invoices_df = invoices_df[invoices_df[Basic.status] == InvoStatus.success]
    chunks = [row.Products for row in invoices_df.itertuples()]
    products = list(itertools.chain.from_iterable(chunks))
    products_df = pd.DataFrame(products).drop(["Name", "Quantity"], axis = 1)
    return products_df


def _enrich_product_prices(price_df, products_df):
    """ Add prices to the products list.

    :param price_df: pandas dataframe, prices from odoo server.
    :param products_df: pandas dataframe, products of invoices.
    :return: pandas dataframe, combined dataframes.
    """
    df = products_df.merge(price_df, how = "left", indicator = Basic.found_in, left_on = InvoField.part_code,
                           right_on = OdooLabel.internal_id)
    df = df[df[Basic.found_in] == "both"]
    return df


def _calculate_status(row):
    """ Calculate price fluctuations of each product.

    :param row: pandas series, each product.
    :return: pandas series, updated product.
    """
    price = row["Unit Cost"]
    old_price = row["Old Sales Price"]
    if price > old_price:
        status = PriceStatus.up
    elif price < old_price:
        status = PriceStatus.down
    else:
        status = PriceStatus.equal
    row["Status"] = status
    return row


def update_product_prices():
    """ Update prices in price-tp.csv file to be able to imported to the Odoo server.
    """
    log.info("Update Third-Party product prices.")
    price_file = f"{get_files().get_price()}.{DocExt.csv}"
    historical_file_path = mk_dir(curr_his_dir, f"{price_file}")
    price_df = pd.read_csv(f"{PRICE_DIR}/{price_file}")
    products_df = _extract_invoice_products()
    enriched_df = _enrich_product_prices(price_df, products_df)
    enriched_df = enriched_df.apply(_calculate_status, axis = 1)
    write_to_csv(historical_file_path, enriched_df,
                 columns = ["External ID", "Internal Reference", "Old Sales Price", "Old Cost", "Unit Cost",
                            "Unit Cost", "Status"],
                 header = ["External ID", "Internal Reference", "Old Sales Price", "Old Cost", "Sales Price",
                           "Cost", "Status"])
