import multibajajmgt.client.odoo.client as odoo_client
import pandas as pd

from loguru import logger as log
from multibajajmgt.app import App
from multibajajmgt.common import (csvstr_to_df, get_dated_dir, get_files, get_now_file, mk_dir, write_to_csv)
from multibajajmgt.config import STOCK_DIR, INVOICE_HISTORY_DIR, ADJUSTMENT_DIR
from multibajajmgt.enums import (
    BasicFieldName as Basic,
    DocumentResourceExtension as DocExt,
    InvoiceField as InvoField,
    InvoiceStatus as Status,
    OdooFieldLabel as OdooLabel,
    OdooFieldValue as OdooValue,
    POSParentCategory as POSCateg,
)

curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_adj_dir = get_dated_dir(ADJUSTMENT_DIR)


def export_products():
    """ Fetch, process and save stock.
    """
    pos_categ = App.get_app().get_pos_categ()
    log.info("Export stock: {}.", pos_categ)
    # Fetch function depends on app's configured POS category
    raw_data = odoo_client.fetch_dpmc_stock() if pos_categ == POSCateg.dpmc else odoo_client.fetch_all_stock()
    product_df = csvstr_to_df(raw_data)
    write_to_csv(f"{STOCK_DIR}/{get_files().get_stock()}.{DocExt.csv}", product_df)


def _validate_products(products_df):
    """ Product is marked as invalid if its ID doesn't exist in the stock_*_*.csv file.

    :param products_df: pandas dataframe, products of an invoice.
    :return: pandas dataframe, validated data.
    """
    for product in products_df.itertuples():
        if product.FoundIn == "left_only":
            products_df = products_df.drop(product.Index)
            log.warning("Failed to validate product: {}.", product.ID)
    products_df.drop(Basic.found_in, axis = 1, inplace = True)
    products_df.reset_index(drop = True, inplace = True)
    return products_df


def _merge_duplicates(products):
    """ Merge Quantities, and drop duplicate Products.

    :param products: list, products.
    :return: pandas dataframe, products without duplicates.
    """
    log.debug("Remove duplicate products.")
    df = pd.DataFrame(products)
    df["Quantity"] = df.groupby(["ID"])["Quantity"].transform('sum')
    df.drop_duplicates(["ID"], keep = "last", inplace = True)
    return df


def _enrich_invoice(row, stock_df):
    """ Add basic info and stock data to each invoice.

        1. Break invoice rows into product rows.
            Currently, each specific invoice has a row with a column containing a list of its products. These products
            need to have its own specific row for further calculations.
        2. Add the necessary columns(like `name`, `Accounting Date`, etc.)
        3. Add the stock data(identification data from Odoo server).

    :param row: itertuple, single invoice.
    :param stock_df: pandas dataframe, stock data.
    :return: pandas dataframe, enriched df.
    """
    # Merge product duplicates
    products_df = _merge_duplicates(row.Products)
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

    :param product: itertuple, product from adjustment.
    :param adjustment_df: pandas dataframe, all adjustments.
    """
    diff_qty = int(product.Quantity)
    stock_qty = product.Quantity_On_Hand
    counted_qty = stock_qty + diff_qty
    adjustment_df.at[product.Index, OdooLabel.adj_prod_counted_qty] = counted_qty
    # Log issues with the calculations due to invalid quantities from Odoo server
    if stock_qty < 0:
        # Product already has negative qty
        log.warning("Initial quantity is negative for {}. Stock: {}. Difference: {}. Counted: {}.",
                    product.ID, stock_qty, diff_qty, counted_qty)
    elif counted_qty < 0:
        # Negative difference is larger than existing product qty
        log.warning("Final quantity is negative for {}. Stock: {}. Difference: {}. Counted: {}.",
                    product.ID, stock_qty, diff_qty, counted_qty)


def create_adjustment():
    """ Retrieve information from data/invoice and create the appropriate adjustment.
    """
    log.info("Create adjustments.")
    adjustments = []
    stock_df = pd.read_csv(f"{STOCK_DIR}/{get_files().get_stock()}.{DocExt.csv}")
    invoice_df = pd.read_json(f"{curr_invoice_dir}/{get_files().get_invoice()}.{DocExt.json}", orient = 'records',
                              convert_dates = False)
    adjustment_file = mk_dir(curr_adj_dir, get_now_file(DocExt.csv, get_files().get_adj()))
    # Filter and sort invoices with successful status
    invoice_df = invoice_df[invoice_df[Basic.status] == Status.success] \
        .sort_values(by = [InvoField.date, InvoField.default_id])
    # Merge invoice duplicates
    invoice_df = invoice_df.groupby(["Date", "ID"], as_index = False).sum()
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
