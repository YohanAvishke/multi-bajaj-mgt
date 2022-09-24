import logging
import sys

import pandas as pd
import multibajajmgt.clients.odoo.client as odoo_client
import multibajajmgt.clients.dpmc.client as dpmc_client

from multibajajmgt.common import write_to_csv
from multibajajmgt.config import DATA_DIR
from multibajajmgt.enums import (
    DocumentResourceType, OdooFieldName
)

log = logging.getLogger(__name__)

PRICE_DPMC_ALL_FILE = f"{DATA_DIR}/price/{DocumentResourceType.price_dpmc_all}"


def export_all_dpmc_products():
    """
    Fetch and save all(qty >= 0 and qty < 0) dpmc product price
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
    write_to_csv(
            PRICE_DPMC_ALL_FILE, enrich_price_df, ["external_id", "default_code", "list_price", "standard_price"],
            [OdooFieldName.external_id, OdooFieldName.internal_id, "Old Sales Price", "Old Cost"])


def _update_dpmc_product_price(price_row):
    try:
        ref_id = price_row["Internal Reference"]
        # Fetch new price
        product_data = dpmc_client.inquire_product_data(ref_id)
        price = product_data["DATA"]["dblSellingPrice"]
        price_row["Sales Price"] = price_row["Cost"] = price
        # Calculate status
        if price_row["Sales Price"] > price:
            price_row["Status"] = "down"
        elif price_row["Sales Price"] < price:
            price_row["Status"] = "up"
        else:
            price_row["Status"] = "equal"
        logging.info(f"{price_row.name + 1} - Product Number: {ref_id}, Price: {price}")
    except Exception as e:
        log.error("Issue occurred while fetching a product's price: ", e)
        sys.exit(0)


def update_dpmc_product_prices():
    price_df = pd.read_csv(PRICE_DPMC_ALL_FILE)
    # Add columns for updated prices and price fluctuation state
    if OdooFieldName.sales_price not in price_df.columns:
        price_df[OdooFieldName.sales_price] = price_df[OdooFieldName.cost] = price_df["Status"] = None
        write_to_csv(path = PRICE_DPMC_ALL_FILE, df = price_df)
    # Loop and fetch and save each product's updated price
    product_df = price_df.apply(_update_dpmc_product_price, axis = 1)
