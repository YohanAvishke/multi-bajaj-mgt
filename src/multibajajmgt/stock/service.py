import logging

import pandas as pd
import multibajajmgt.clients.odoo.client as odoo_client

from multibajajmgt.config import STOCK_HISTORY_DIR
from multibajajmgt.common import *
from multibajajmgt.enums import (
    InvoiceJSONFieldName as JSONField,
    InvoiceStatus as Status,
    OdooCSVFieldName as CSVField,
    OdooDBFieldName as DBField
)

log = logging.getLogger(__name__)


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
    write_to_csv(STOCK_HISTORY_DIR, enrich_product_df,
                 columns = [DBField.external_id, DBField.internal_id, DBField.qty_available],
                 header = [CSVField.external_id, CSVField.internal_id, CSVField.qty_available])


def create_adjustment(invoice_dir, invoice_file):
    invoice_df = pd.read_json(invoice_file, orient = 'records', convert_dates = False)
    invoice_df = invoice_df[invoice_df[JSONField.status] == Status.success] \
        .sort_values(by = [JSONField.date, JSONField.invoice_id])

    # with open(DATED_ADJUSTMENT_FILE, "w") as adj_csv_file:
    #     field_names = ("name", "Accounting Date", "Product/Internal Reference", "Counted Quantity")
    #     adj_writer = csv.DictWriter(adj_csv_file, fieldnames = field_names, delimiter = ',', quotechar = '"',
    #                                 quoting = csv.QUOTE_MINIMAL)
    #     adj_writer.writeheader()
    #     for adjustment in sorted_adjustment:
    #         for product in adjustment["Products"]:
    #             product_number = product["STR_PART_NO"] if "STR_PART_NO" in product else product["STR_PART_CODE"]
    #             product_count = product["INT_QUANTITY"] if "INT_QUANTITY" in product else product["INT_QUATITY"]
    #
    #             adj_writer.writerow({"name": adjustment["ID"],
    #                                  "Accounting Date": adjustment["Date"],
    #                                  "Product/Internal Reference": product_number,
    #                                  "Counted Quantity": float(product_count)})
