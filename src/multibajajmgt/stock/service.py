import logging

import pandas as pd
import multibajajmgt.clients.odoo.client as odoo_client

from multibajajmgt.app import App
from multibajajmgt.common import *
from multibajajmgt.config import STOCK_DIR, INVOICE_HISTORY_DIR, ADJUSTMENT_DIR
from multibajajmgt.enums import (
    BasicFieldName as Field,
    DocumentResourceExtension as DRExt,
    DocumentResourceName as DRName,
    InvoiceStatus as Status,
    OdooCSVFieldName as OdooField,
    OdooCSVFieldValue as OdooFieldVal,
    OdooDBFieldName as DBField,
    POSParentCategory as POSCatg
)

log = logging.getLogger(__name__)
curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_adj_dir = get_dated_dir(ADJUSTMENT_DIR)


def _evaluate_pos_category():
    """ Map client fetching function for the pos_category.

    :return: function, (func reference, stock file path, invoice file path)
    """
    categ = App().get_pos_categ()
    if categ == POSCatg.dpmc:
        return odoo_client.fetch_all_dpmc_stock, \
               f"{STOCK_DIR}/{DRName.stock_dpmc_all}.{DRExt.csv}", \
               f"{curr_invoice_dir}/{DRName.invoice_dpmc}.{DRExt.json}"

    elif categ == POSCatg.other:
        return odoo_client.fetch_all_thirdparty_stock, \
               f"{STOCK_DIR}/{DRName.stock_other_all}.{DRExt.csv}", \
               f"{curr_invoice_dir}/{DRName.invoice_sales}.{DRExt.json}"
    else:
        return odoo_client.fetch_all_stock, \
               f"{STOCK_DIR}/{DRName.stock_all}.{DRExt.csv}", \
               f"{curr_invoice_dir}/{DRName.invoice_sales}.{DRExt.json}"


def _enrich_products_by_id(product_df, prod_prod_ids):
    """ Merge the two dfs together, to add external id for each product.

    :param product_df: panda dataframe, product data
    :param prod_prod_ids: pandas dataframe, ids fetched by `product.product`
    :return: pandas dataframe, finalised(merged) dataframe
    """
    prod_prod_id_df = pd.DataFrame(prod_prod_ids)
    # Aggregate `module and name`, drop and rename columns
    prod_prod_id_df[DBField.external_id] = \
        prod_prod_id_df[[DBField.ir_model_module, DBField.ir_model_name]].agg(".".join, axis = 1)
    prod_prod_id_df = prod_prod_id_df \
        .drop([DBField.id, DBField.ir_model_name, DBField.ir_model_module], axis = 1) \
        .rename({DBField.res_id: DBField.id}, axis = 1)
    # Merge ids into product df
    enriched_prod_df = product_df.merge(prod_prod_id_df, on = DBField.id, how = "inner")
    return enriched_prod_df


def export_products():
    """ Fetch, process and save full DPMC stock.
    """
    fetch_func_ref, stock_file, invoice_file = _evaluate_pos_category()
    # Fetch dpmc stock
    products = fetch_func_ref()
    product_df = pd.DataFrame(products)
    # Extract tmpl_id and re-save it
    tmpl_id_df = pd.DataFrame(product_df[DBField.tmpl_id].tolist())[0]
    product_df[DBField.tmpl_id] = tmpl_id_df
    # Fetch qty of each product in stock
    qty_data = odoo_client.fetch_product_quantity(tmpl_id_df.to_list())
    qty_df = pd.DataFrame(qty_data).rename(columns = {DBField.id: DBField.tmpl_id})
    # Merge qty with stock
    product_df = product_df.merge(qty_df, on = DBField.tmpl_id, how = "inner")
    # Fetch product's external id lists
    prod_prod_ids = odoo_client.fetch_product_external_id(product_df[DBField.id].to_list(), "product.product")
    # Merge external ids with stock
    enrich_product_df = _enrich_products_by_id(product_df, prod_prod_ids)
    write_to_csv(stock_file, enrich_product_df,
                 columns = [DBField.external_id, DBField.internal_id, DBField.qty_available],
                 header = [OdooField.external_id, OdooField.internal_id, OdooField.qty_available])


def _enrich_invoice_with_stock_info(row, stock_df):
    """ Add basic info and stock data to each invoice.

    :param row: itertuple, single invoice
    :param stock_df: pandas dataframe, stock data
    :return: pandas dataframe, enriched df
    """
    product_df = pd.json_normalize(row.Products)
    # Create basic invoice columns which share common data within all products of an invoice
    # index should [0] to make sure common data is only stored in the first row of each adjustment
    product_df[[OdooField.adj_name,
                OdooField.adj_acc_date,
                OdooField.is_exh_products]] = pd.DataFrame([[row.ID,
                                                             row.Date,
                                                             True, ]], index = [0])
    # Set location id to all the products
    product_df[OdooField.adj_loc_id] = OdooFieldVal.adj_loc_id
    # Add columns from stock data to the products
    product_df = product_df.merge(stock_df, how = "inner",
                                  left_on = Field.part_code, right_on = OdooField.internal_id)
    return product_df


def _calculate_counted_qty(row, adjustment_df):
    """ Calculate final quantities for each product in adjustment.

    :param row: itertuple, product from adjustment
    :param adjustment_df: pandas dataframe, all adjustments
    """
    diff_qty = int(row.Quantity)
    stock_qty = row.QuantityOnHand
    counted_qty = stock_qty + diff_qty
    adjustment_df.at[row.Index, OdooField.adj_prod_counted_qty] = counted_qty
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
    adjustment_file = mk_dir(curr_adj_dir, get_now_file(DRExt.csv, DRName.adjustment_dpmc))
    adjustments = []
    func, stock_file, invoice_file = _evaluate_pos_category()
    stock_df = pd.read_csv(stock_file)
    invoice_df = pd.read_json(invoice_file, orient = 'records', convert_dates = False)
    # Filter and sort invoices with successful status
    invoice_df = invoice_df[invoice_df[Field.status] == Status.success] \
        .sort_values(by = [Field.date, Field.default_id])
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
                 columns = [OdooField.adj_name, OdooField.adj_acc_date, OdooField.is_exh_products, "ID",
                            OdooField.external_id, OdooField.adj_loc_id, OdooField.adj_prod_counted_qty],
                 header = [OdooField.adj_name, OdooField.adj_acc_date, OdooField.is_exh_products, "product_id",
                           OdooField.adj_prod_external_id, OdooField.adj_loc_id, OdooField.adj_prod_counted_qty])
