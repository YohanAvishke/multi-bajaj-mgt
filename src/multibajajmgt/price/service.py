import logging
import pandas as pd

import multibajajmgt.clients.odoo as odoo_client

from multibajajmgt.logger import configure_logging
from multibajajmgt.config import DATA_DIR
from multibajajmgt.common import write_to_csv

log = logging.getLogger(__name__)


def export_all_dpmc_products():
    """

    :return:
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
    write_to_csv(DATA_DIR + "/price/" + "price.dpmc.all.csv", enrich_price_df,
                 ["external_id", "default_code", "list_price", "standard_price"],
                 ["External ID", "Internal Reference", "Sales Price", "Cost"])


if __name__ == "__main__":
    configure_logging()
    export_all_dpmc_products()
