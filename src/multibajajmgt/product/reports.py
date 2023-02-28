import pandas as pd

from loguru import logger as log
from multibajajmgt.common import get_files, write_to_csv
from multibajajmgt.config import PRODUCT_DIR, STOCK_DIR
from multibajajmgt.enums import (
    DocumentResourceExtension as DocExt,
    DocumentResourceName as DocName,
    OdooFieldLabel as OdooLabel,
    ProductEnrichmentCategories as ProdEnrichCateg
)


def enrich(*enrichments: ProdEnrichCateg):
    log.info(f"Enrich products from {enrichments}.")
    stock_df = pd.read_csv(f"{STOCK_DIR}/{get_files().get_stock()}.{DocExt.csv}")
    stock_df = stock_df.drop("Product/Product/ID", axis = 1)
    product_df = pd.read_csv(f"{PRODUCT_DIR}/{DocName.product}.{DocExt.csv}")
    enriched_df = product_df \
        .merge(stock_df, how = "left", on = OdooLabel.internal_id) \
        .rename(columns = {"Quantity_On_Hand": "Bajaj"})
    enriched_df["YL ref"] = enriched_df.apply(lambda x: f"{x[OdooLabel.internal_id]}(YL)", axis = 1)
    enriched_df = enriched_df.merge(stock_df, how = "left", left_on = "YL ref", right_on = OdooLabel.internal_id)
    enriched_df = enriched_df \
        .rename(columns = {"Internal Reference_x": "Internal Reference", "Quantity_On_Hand": "YL"}) \
        .drop(["YL ref", "Internal Reference_y"], axis = 1) \
        .fillna(0)
    write_to_csv(f"{PRODUCT_DIR}/{DocName.product}.{DocExt.csv}", enriched_df)
