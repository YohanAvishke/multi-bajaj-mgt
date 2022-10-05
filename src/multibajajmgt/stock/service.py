import logging

import pandas as pd
import multibajajmgt.clients.odoo.client as odoo_client

from multibajajmgt.config import DATA_DIR
from multibajajmgt.common import *
from multibajajmgt.enums import (
    DocumentResourceType,
    OdooCSVFieldName as CSVField,
    OdooDBFieldName as DBField
)

log = logging.getLogger(__name__)

STOCK_BASE_FILE = f"{DATA_DIR}/stock/{DocumentResourceType.stock_dpmc_all}"


def export_all_products():
    # Fetch dpmc stock
    products = odoo_client.fetch_all_dpmc_stock()
    product_df = pd.DataFrame(products)
    ids = product_df["id"].tolist()
    # Fetch dpmc product's external id list
    ex_ids = odoo_client.fetch_product_external_id(ids)
    ex_id_df = pd.DataFrame(ex_ids)
    # Drop external ids duplicates, if any
    ex_id_df = drop_duplicates(ex_id_df, "res_id")
    # Merge products with external ids
    enrich_product_df = enrich_products_by_external_id(product_df, ex_id_df)
    write_to_csv(STOCK_BASE_FILE, enrich_product_df,
                 columns = [DBField.external_id, DBField.internal_id, DBField.qty_available],
                 header = [CSVField.external_id, CSVField.internal_id, CSVField.qty_available])
