import logging

import pandas as pd
import multibajajmgt.clients.odoo.client as odoo_client

from multibajajmgt.config import STOCK_DIR, INVOICE_HISTORY_DIR, ADJUSTMENT_DIR
from multibajajmgt.common import *
from multibajajmgt.enums import (
    DocumentResourceType as DRType,
    DocumentResourceExtension as DRExt,
    InvoiceJSONFieldName as JSONField,
    InvoiceStatus as Status,
    OdooCSVFieldName as CSVField,
    OdooDBFieldName as DBField
)

log = logging.getLogger(__name__)
curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_adj_dir = get_dated_dir(ADJUSTMENT_DIR)
invoice_file = f"{curr_invoice_dir}/{DRType.invoice_dpmc}.{DRExt.json}"
stock_file = f"{STOCK_DIR}/{DRType.stock_dpmc_all}.{DRExt.csv}"


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
    write_to_csv(stock_file, enrich_product_df,
                 columns = [DBField.external_id, DBField.internal_id, DBField.qty_available],
                 header = [CSVField.external_id, CSVField.internal_id, CSVField.qty_available])


# .sort_values(by = [JSONField.date, JSONField.invoice_id])
def create_adjustment():
    adjustment_file = mk_dir(curr_adj_dir, get_now_file(DRExt.csv, DRType.adjustment_dpmc))
    adjustments = []
    stock_df = pd.read_csv(stock_file)
    invoice_df = pd.read_json(invoice_file, orient = 'records', convert_dates = False)
    invoice_df = invoice_df[invoice_df[JSONField.status] == Status.success]
    for invoice_row in invoice_df.itertuples():
        invoice_product_df = pd.json_normalize(invoice_row.Products)
        invoice_product_df[[CSVField.adj_name, CSVField.adj_acc_date, CSVField.is_exh_products]] = \
            pd.DataFrame([[invoice_row[4], invoice_row[1], True]], index = [0])
        invoice_product_df = invoice_product_df.merge(stock_df, how = "inner",
                                                      left_on = JSONField.part_code, right_on = CSVField.internal_id)
        adjustments.append(invoice_product_df)
    adjustment_df = pd.concat(adjustments).reset_index(drop = True)
    adjustment_df[CSVField.adj_loc_id] = "stock.stock_location_stock"
    for adjustment_row in adjustment_df.itertuples():
        diff_qty = adjustment_row.Quantity
        stock_qty = int(adjustment_row[11])
        counted_qty = stock_qty + diff_qty
        adjustment_df.at[adjustment_row.Index, CSVField.adj_prod_counted_qty] = counted_qty
        if stock_qty < 0:
            log.warning(f"Initial quantity is negative for {adjustment_row.ID}. "
                        f"Stock: {stock_qty}. Difference: {diff_qty}. Counted: {counted_qty}.")
        elif counted_qty < 0:
            log.warning(f"Final quantity is negative for {adjustment_row.ID}. "
                        f"Stock: {stock_qty}. Difference: {diff_qty}. Counted: {counted_qty}.")
    write_to_csv(path = adjustment_file, df = adjustment_df,
                 columns = [CSVField.adj_name, CSVField.adj_acc_date, CSVField.is_exh_products,
                            CSVField.external_id, CSVField.adj_loc_id, CSVField.adj_prod_counted_qty],
                 header = [CSVField.adj_name, CSVField.adj_acc_date, CSVField.is_exh_products,
                           CSVField.adj_prod_external_id, CSVField.adj_loc_id, CSVField.adj_prod_counted_qty])
