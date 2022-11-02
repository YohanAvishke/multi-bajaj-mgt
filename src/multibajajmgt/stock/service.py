import pandas as pd
import multibajajmgt.client.odoo.client as odoo_client

from loguru import logger as log
from multibajajmgt.app import App
from multibajajmgt.common import *
from multibajajmgt.config import STOCK_ALL_FILE, INVOICE_HISTORY_DIR, ADJUSTMENT_DIR
from multibajajmgt.enums import (
    BasicFieldName as Basic,
    DocumentResourceExtension as DRExt,
    DocumentResourceName as DRName,
    InvoiceField as InvoField,
    InvoiceStatus as Status,
    OdooFieldLabel as OdooLabel,
    OdooFieldValue as OdooValue,
    POSParentCategory as POSCatg,
)

curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_adj_dir = get_dated_dir(ADJUSTMENT_DIR)


def _evaluate_pos_category():
    """ Map client fetching function for the pos_category.

    :return: function, (func reference, invoice file path, adjustment historical file path)
    """
    categ = App().get_pos_categ()
    if categ == POSCatg.dpmc:
        return f"{curr_invoice_dir}/{DRName.invoice_dpmc}.{DRExt.json}", \
               f"{DRName.adjustment_dpmc}"
    elif categ == POSCatg.tp:
        return f"{curr_invoice_dir}/{DRName.invoice_tp}.{DRExt.json}", \
               f"{DRName.adjustment_tp}"
    elif categ == POSCatg.sales:
        return f"{curr_invoice_dir}/{DRName.invoice_sales}.{DRExt.json}", \
               f"{DRName.adjustment_sales}"


def export_products():
    """ Fetch, process and save stock.
    """
    raw_data = odoo_client.fetch_all_stock()
    product_df = csvstr_to_df(raw_data)
    write_to_csv(STOCK_ALL_FILE, product_df)


def _validate_products(products_df):
    """ Product is marked as invalid if its ID doesn't exist in the stock_*_*.csv file.

    :param products_df: pandas dataframe, products of an invoice
    :return: pandas dataframe, validated data
    """
    for product in products_df.itertuples():
        if product.FoundIn == "left_only":
            products_df = products_df.drop(product.Index)
            log.warning(f"Invalid product found with Id {product.ID}.")
    products_df.drop(Basic.found_in, axis = 1, inplace = True)
    products_df.reset_index(drop = True, inplace = True)
    return products_df


def _enrich_invoice(row, stock_df):
    """ Add basic info and stock data to each invoice.

        1. Break invoice rows into product rows.
            Currently, each specific invoice has a row with a column containing a list of its products. These products
            need to have its own specific row for further calculations.
        2. Add the necessary columns(like `name`, `Accounting Date`, etc.)
        3. Add the stock data(identification data from Odoo server).

    :param row: itertuple, single invoice
    :param stock_df: pandas dataframe, stock data
    :return: pandas dataframe, enriched df
    """
    products_df = pd.json_normalize(row.Products)
    # Add columns from stock data to the products
    # noinspection PyTypeChecker
    products_df = products_df.merge(stock_df, how = "left", indicator = Basic.found_in,
                                    left_on = InvoField.part_code, right_on = OdooLabel.internal_id)
    # Validate the values in indicator and if all products of the invoice are invalid, then return None
    products_df = _validate_products(products_df)
    if len(products_df) == 0:
        return
    # Create basic invoice columns which share common data within all products of an invoice
    # index should [0] to make sure common data is only stored in the first row of each adjustment
    products_df[[OdooLabel.adj_name,
                 OdooLabel.adj_acc_date,
                 OdooLabel.is_exh_products]] = pd.DataFrame([[row.ID,
                                                              row.Date,
                                                              True]], index = [0])
    # Set location id to all the products
    products_df[OdooLabel.adj_loc_id] = OdooValue.adj_loc_id
    return products_df


def _calculate_counted_qty(product, adjustment_df):
    """ Calculate final quantities for each product in adjustment.

    :param product: itertuple, product from adjustment
    :param adjustment_df: pandas dataframe, all adjustments
    """
    diff_qty = int(product.Quantity)
    stock_qty = product[8]
    counted_qty = stock_qty + diff_qty
    adjustment_df.at[product.Index, OdooLabel.adj_prod_counted_qty] = counted_qty
    # Log issues with the calculations due to invalid quantities from Odoo server
    if stock_qty < 0:
        # Product already has negative qty
        log.warning(f"Initial quantity is negative for {product.ID}. "
                    f"Stock: {stock_qty}. Difference: {diff_qty}. Counted: {counted_qty}.")
    elif counted_qty < 0:
        # Negative difference is larger than existing product qty
        log.warning(f"Final quantity is negative for {product.ID}. "
                    f"Stock: {stock_qty}. Difference: {diff_qty}. Counted: {counted_qty}.")


def create_adjustment():
    """ Retrieve information from data/invoice and create the appropriate adjustment.
    """
    evaluations = _evaluate_pos_category()
    adjustments = []
    adjustment_file = mk_dir(curr_adj_dir, get_now_file(DRExt.csv, evaluations[1]))
    stock_df = pd.read_csv(STOCK_ALL_FILE)
    invoice_df = pd.read_json(evaluations[0], orient = 'records', convert_dates = False)
    # Filter and sort invoices with successful status
    invoice_df = invoice_df[invoice_df[Basic.status] == Status.success] \
        .sort_values(by = [InvoField.date, InvoField.default_id])
    for invoice_row in invoice_df.itertuples():
        adjustments.append(_enrich_invoice(invoice_row, stock_df))
    # Append all adjustments into a dataframe
    adjustment_df = pd.concat(adjustments).reset_index(drop = True)
    # Calculate final quantities for each product in adjustment
    for row in adjustment_df.itertuples():
        # _validate_product(row, adjustment_df)
        _calculate_counted_qty(row, adjustment_df)
    # Save data
    write_to_csv(path = adjustment_file, df = adjustment_df,
                 columns = [OdooLabel.adj_name, OdooLabel.adj_acc_date, OdooLabel.is_exh_products,
                            OdooLabel.internal_id, OdooLabel.prod_var_id, OdooLabel.adj_loc_id,
                            OdooLabel.adj_prod_counted_qty],
                 header = [OdooLabel.adj_name, OdooLabel.adj_acc_date, OdooLabel.is_exh_products, "InternalReference",
                           OdooLabel.adj_prod_external_id, OdooLabel.adj_loc_id, OdooLabel.adj_prod_counted_qty])
