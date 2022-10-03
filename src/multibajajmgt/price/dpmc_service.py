import logging
import os

import pandas as pd
import multibajajmgt.clients.odoo.client as odoo_client
import multibajajmgt.clients.dpmc.client as dpmc_client

from multibajajmgt.common import *
from multibajajmgt.config import DATA_DIR
from multibajajmgt.enums import (
    DocumentResourceType,
    OdooCSVFieldName as CSVField,
    OdooDBFieldName as DBField,
    ProductPriceStatus as Status
)
from multibajajmgt.exceptions import InvalidIdentityError

log = logging.getLogger(__name__)

PRICE_ALL_BASE_FILE = f"{DATA_DIR}/price/{DocumentResourceType.price_dpmc_all}"
PRICE_HISTORY_DIR = f"{DATA_DIR}/price/history"


def export_all_products():
    """ Fetch and Save all(qty >= 0 and qty < 0) DPMC product prices from Odoo server.
    """
    # Fetch dpmc product's price list
    prices = odoo_client.fetch_all_dpmc_prices()
    price_df = pd.DataFrame(prices)
    ids = price_df["id"].tolist()
    # Fetch dpmc product's external id list
    ex_ids = odoo_client.fetch_product_external_id(ids)
    ex_id_df = pd.DataFrame(ex_ids)
    # Drop external ids duplicates, if any
    ex_id_df["is_duplicate"] = ex_id_df.duplicated(subset = ['res_id'], keep = False)
    duplicate_df = ex_id_df[ex_id_df['is_duplicate']]
    if duplicate_df.size > 0:
        log.warning(f"Filtering duplicates,\n {duplicate_df}")
        ex_id_df = ex_id_df.drop_duplicates(subset = ["res_id"], keep = "first")
    # Enrich the price list by,
    #   * Create external id
    #   * Drop and rename columns
    #   * Merge price list and external id list(by id)
    ex_id_df["external_id"] = ex_id_df[["module", "name"]].agg('.'.join, axis = 1)
    ex_id_df = ex_id_df \
        .drop(["id", "name", "module", "is_duplicate"], axis = 1) \
        .rename({"res_id": "id"}, axis = 1)
    enrich_price_df = ex_id_df.merge(price_df, on = "id", how = "inner")
    write_to_csv(PRICE_ALL_BASE_FILE, enrich_price_df,
                 columns = [DBField.external_id, DBField.internal_id, DBField.sales_price, DBField.cost],
                 header = [CSVField.external_id, CSVField.internal_id, "Old Sales Price", "Old Cost"])


def _get_price_info(row):
    """ Fetch price data from DPMC server.

    :param row: itertuples obj, each row of price df.
    :return: dict, necessary information for a price update to be completed.
    """
    index = row.Index
    ref_id = row[2]  # getattr(row, DBField.internal_id)
    old_price = row[4]  # getattr(row, DBField.cost)
    status = Status.none
    try:
        # Fetch new price
        product_data = dpmc_client.inquire_product_data(ref_id)
    except InvalidIdentityError:
        # Duplicate existing price since the data fetching failed
        price = old_price
        process_status = "Failed"
    else:
        price = float(product_data["dblSellingPrice"])
        # Calculate and save status
        if price > old_price:
            status = Status.up
        elif price < old_price:
            status = Status.down
        else:
            status = Status.equal
        process_status = "Success"
    return {
        "index": index,
        "ref_id": ref_id,
        "updated_price": price,
        "price_status": status,
        "process_status": process_status
    }


def _save_price_info(info, df, dir_path):
    """ Save new price information to price-dpmc-all.csv(base file) and time based historical file.

    :param info: dict, necessary information for a price update to be completed.
    :param df: pandas dataframe, dataframe with data of base file.
    """
    index = info["index"]
    price = info["updated_price"]
    status = info["price_status"]
    # Save price and status
    df.at[index, CSVField.sales_price] = df.at[index, CSVField.cost] = price
    df.at[index, "Status"] = status
    # Save row to base csv file
    write_to_csv(PRICE_ALL_BASE_FILE, df)
    # Save row to historic csv file
    if status in (Status.up, Status.down):
        file = mk_historical(dir_path, get_now_file("csv", "price-dpmc-all"))
        # Get the row as a series. Convert it to a df and flip the row and column
        row_transposed = df.loc[index].to_frame().T
        write_to_csv(path = file, df = row_transposed, mode = "a",
                     header = not os.path.exists(file))
    logging.info(f"{index + 1} - {info['process_status']} - Product Number: {info['ref_id']}, Price: {price}")


def update_product_prices():
    """ Update prices in price-dpmc-all.csv file to be able to imported to the Odoo server.
    """
    price_df = pd.read_csv(PRICE_ALL_BASE_FILE)
    curr_dir = get_curr_dir(f"{DATA_DIR}/price/history")
    # Add columns for updated prices and price fluctuation state
    if CSVField.sales_price not in price_df.columns:
        price_df[CSVField.sales_price] = price_df[CSVField.cost] = price_df["Status"] = None
        write_to_csv(path = PRICE_ALL_BASE_FILE, df = price_df)
    price_updatable_df = price_df[pd.isnull(price_df['Status'])]
    # Loop and fetch and save each product's updated price
    for price_row in price_updatable_df.itertuples():
        # Filter rows with non-updated price and status
        if pd.isnull(price_row[7]):
            info = _get_price_info(price_row)
            _save_price_info(info, price_df, curr_dir)


def merge_historical_data():
    return
