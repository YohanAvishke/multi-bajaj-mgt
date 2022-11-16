import os
import pandas as pd
import multibajajmgt.client.odoo.client as odoo_client
import multibajajmgt.client.dpmc.client as dpmc_client

from loguru import logger as log
from multibajajmgt.common import csvstr_to_df, get_dated_dir, get_files, get_now_file, mk_dir, write_to_csv
from multibajajmgt.config import PRICE_DIR, PRICE_HISTORY_DIR
from multibajajmgt.enums import (
    BasicFieldName as BaseField,
    DocumentResourceExtension as DocExt,
    PriceField,
    ProductPriceStatus as Status
)
from multibajajmgt.exceptions import InvalidIdentityError
from pathlib import Path

curr_his_dir = get_dated_dir(PRICE_HISTORY_DIR)


def export_prices():
    """ Fetch and Save all(qty >= 0 and qty < 0) DPMC product prices.
    """
    log.info("Exporting DPMC prices from odoo server")
    raw_data = odoo_client.fetch_all_dpmc_prices()
    products = csvstr_to_df(raw_data)
    write_to_csv(f"{PRICE_DIR}/{get_files().get_price()}.{DocExt.csv}", products)


def _get_price_info(row):
    """ Fetch price data from DPMC server.

    :param row: iter-tuples obj, each row of price df
    :return: dict, necessary information for a price update to be completed
    """
    index = row.Index
    ref_id = row[2]  # getattr(row, OdooName.internal_id)
    old_price = row[4]  # getattr(row, OdooName.cost)
    status = Status.none
    try:
        # Fetch new price
        product_data = dpmc_client.inquire_product_price(ref_id)
    except InvalidIdentityError:
        # Duplicate existing price since the data fetching failed
        price = old_price
        process_status = "Failed"
    else:
        price = product_data["INT_UNIT_COST"]
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


def _save_price_info(info, df, file):
    """ Save new price information to price-dpmc-all.csv(base file) and time based historical file.

    :param info: dict, necessary information for a price update to be completed
    :param df: pandas dataframe, dataframe with data of base file
    :param file: string, historical file
    """
    index = info["index"]
    price = info["updated_price"]
    status = info["price_status"]
    # Save price and status
    df.at[index, PriceField.price] = df.at[index, PriceField.cost] = price
    df.at[index, BaseField.status] = status
    # Save row to base csv file
    write_to_csv(f"{PRICE_DIR}/{get_files().get_price()}.{DocExt.csv}", df)
    # Save row to historic csv file
    if status in (Status.up, Status.down):
        # Get the row as a series. Convert it to a df and flip the row and column
        row_transposed = df.loc[index].to_frame().T
        write_to_csv(path = file, df = row_transposed, mode = "a", header = not os.path.exists(file))
    log.info(f"{index + 1} - {info['process_status']} - Product Number: {info['ref_id']}, Price: {price}")


def update_product_prices():
    """ Update prices in price-dpmc-all.csv file to be able to imported to the Odoo server.
    """
    log.info("Updating DPMC product's prices")
    price_file = f"{get_files().get_price()}.{DocExt.csv}"
    price_df = pd.read_csv(f"{PRICE_DIR}/{price_file}")
    historical_file_path = mk_dir(curr_his_dir, get_now_file(DocExt.csv, get_files().get_price()))
    # Add columns for updated prices and price fluctuation state
    if BaseField.status not in price_df.columns:
        price_df[PriceField.price] = price_df[PriceField.cost] = price_df[BaseField.status] = None
        write_to_csv(path = f"{PRICE_DIR}/{price_file}", df = price_df)
    price_updatable_df = price_df[pd.isnull(price_df[BaseField.status])]
    # Loop and fetch and save each product's updated price
    for price_row in price_updatable_df.itertuples():
        # Filter rows with non-updated price and status
        if pd.isnull(price_row.Status):
            info = _get_price_info(price_row)
            _save_price_info(info, price_df, historical_file_path)


def merge_historical_data():
    """ Merge timed files in a historical dir
    """
    log.info("Merging historical files of today")
    merged_file = f"{curr_his_dir}/{get_files().get_price()}.{DocExt.csv}"
    # Remove existing merge file
    if os.path.isfile(merged_file):
        os.remove(merged_file)
    # Read, sort, merge and save the new merge file
    files = sorted(Path(curr_his_dir).glob(f"price_dpmc_all_*.{DocExt.csv}"))
    df = pd.concat((pd.read_csv(f).assign(filename = f.stem) for f in files), ignore_index = True)
    write_to_csv(merged_file, df)
    # Remove timed files
    for f in files:
        os.remove(f)
