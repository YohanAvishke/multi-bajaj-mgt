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
    OdooCSVFieldValue as CSVFieldValue,
    OdooDBFieldName as DBField
)

log = logging.getLogger(__name__)
curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_adj_dir = get_dated_dir(ADJUSTMENT_DIR)
invoice_file = f"{curr_invoice_dir}/{DRType.invoice_dpmc}.{DRExt.json}"
stock_file = f"{STOCK_DIR}/{DRType.stock_dpmc_all}.{DRExt.csv}"


def _format_id_df(df):
    """ Create `external_id` column and drop and rename the rest of columns.

    :param df: pandas dataframe
    :return: pandas dataframe
    """
    df["external_id"] = df[["module", "name"]].agg(".".join, axis = 1)
    df = df \
        .drop(["id", "name", "module"], axis = 1) \
        .rename({"res_id": "id"}, axis = 1)
    return df


def _enrich_products_by_id(product_df, ex_ids, prod_prod_ids):
    """ Merge all three dfs together to fill external ids of every single product.

    1. Merge `ex_ids` into `prod_prod_ids`
    2. Merge result of step 1 into `product_df`

    :param product_df: pandas dataframe, products data
    :param ex_ids: pandas dataframe, ids fetched by `product.template`
    :param prod_prod_ids: pandas dataframe, ids fetched by `product.product`
    :return: pandas dataframe, finalised(merged) dataframe
    """
    ex_id_df = pd.DataFrame(ex_ids)
    prod_prod_id_df = pd.DataFrame(prod_prod_ids)
    # Aggregate `module and name`, drop and rename columns
    ex_id_df = drop_duplicates(ex_id_df, DBField.res_id)
    ex_id_df = _format_id_df(ex_id_df)
    prod_prod_id_df = _format_id_df(prod_prod_id_df)
    # Merge 2 different id dfs into one `prod_prod_id_df` gets priority
    id_df = ex_id_df.merge(prod_prod_id_df, on = DBField.id, how = "outer")
    id_df["external_id_y"].fillna(id_df["external_id_x"], inplace = True)
    del id_df['external_id_x']
    id_df.rename({"external_id_y": DBField.external_id}, axis = 1, inplace = True)
    # Merger ids into product df
    enrich_price_df = id_df.merge(product_df, on = DBField.id, how = "inner")
    return enrich_price_df


def export_all_products():
    """ Fetch, process and save full DPMC stock.
    """
    # Fetch dpmc stock
    products = odoo_client.fetch_all_dpmc_stock()
    product_df = pd.DataFrame(products)
    ids = product_df[DBField.id].tolist()
    # Fetch dpmc product's external id lists
    # Since `product.product` doesn't cover all products, it's necessary to fetch `product.template` ids as well
    prod_prod_ids = odoo_client.fetch_product_external_id(ids, "product.product")
    ex_ids = odoo_client.fetch_product_external_id(ids, "product.template")
    # Merge 2 external id lists and then merge with product list
    enrich_product_df = _enrich_products_by_id(product_df, ex_ids, prod_prod_ids)
    write_to_csv(stock_file, enrich_product_df,
                 columns = [DBField.external_id, DBField.internal_id, DBField.qty_available],
                 header = [CSVField.external_id, CSVField.internal_id, CSVField.qty_available])


def _enrich_invoice_with_stock_info(row, stock_df):
    """ Add basic info and stock data to each invoice.

    :param row: itertuple, single invoice from invoices
    :param stock_df: pandas dataframe, stock data
    :return: pandas dataframe, enriched df
    """
    product_df = pd.json_normalize(row.Products)
    # Create basic invoice columns which share common data within all products of an invoice
    product_df[[CSVField.adj_name,
                CSVField.adj_acc_date,
                CSVField.is_exh_products,
                CSVField.adj_loc_id]] = pd.DataFrame([[row[4],
                                                       row.Date,
                                                       True,
                                                       CSVFieldValue.adj_loc_id]], index = [0])
    # Add columns from stock data to the products
    product_df = product_df.merge(stock_df, how = "inner", left_on = JSONField.part_code,
                                  right_on = CSVField.internal_id)
    return product_df


def _calculate_counted_qty(row, adjustment_df):
    """ Calculate final quantities for each product in adjustment.

    :param row: itertuple, product from adjustment
    :param adjustment_df: pandas dataframe, all adjustments
    """
    diff_qty = row.Quantity
    stock_qty = int(row[12])
    counted_qty = stock_qty + diff_qty
    adjustment_df.at[row.Index, CSVField.adj_prod_counted_qty] = counted_qty
    # Log issues with the calculations due to invalid quantities from Odoo server
    if stock_qty < 0:
        # Product already has negative qty
        log.warning(f"Initial quantity is negative for {row.ID}. "
                    f"Stock: {stock_qty}. Difference: {diff_qty}. Counted: {counted_qty}.")
    elif counted_qty < 0:
        # Negative difference is larger than existing product qty
        log.warning(f"Final quantity is negative for {row.ID}. "
                    f"Stock: {stock_qty}. Difference: {diff_qty}. Counted: {counted_qty}.")


def create_adjustment():
    """ Retrieve information from data/invoice and create the appropriate adjustment.
    """
    adjustment_file = mk_dir(curr_adj_dir, get_now_file(DRExt.csv, DRType.adjustment_dpmc))
    adjustments = []
    stock_df = pd.read_csv(stock_file)
    invoice_df = pd.read_json(invoice_file, orient = 'records', convert_dates = False)
    # Filter ans sort invoices with successful status
    invoice_df = invoice_df[invoice_df[JSONField.status] == Status.success] \
        .sort_values(by = [JSONField.date, JSONField.invoice_id])
    # Break and add info to invoices and create an adjustment
    for invoice_row in invoice_df.itertuples():
        adjustments.append(_enrich_invoice_with_stock_info(invoice_row, stock_df))
    # Append all adjustments into a dataframe
    adjustment_df = pd.concat(adjustments).reset_index(drop = True)
    # Calculate final quantities for each product in adjustment
    for adjustment_row in adjustment_df.itertuples():
        _calculate_counted_qty(adjustment_row, adjustment_df)
    # Save data
    write_to_csv(path = adjustment_file, df = adjustment_df,
                 columns = [CSVField.adj_name, CSVField.adj_acc_date, CSVField.is_exh_products, "ID",
                            CSVField.external_id, CSVField.adj_loc_id, CSVField.adj_prod_counted_qty],
                 header = [CSVField.adj_name, CSVField.adj_acc_date, CSVField.is_exh_products, "product_id",
                           CSVField.adj_prod_external_id, CSVField.adj_loc_id, CSVField.adj_prod_counted_qty])
