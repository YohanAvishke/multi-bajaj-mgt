import multibajajmgt.client.dpmc.client as dpmc_client
import pandas as pd

from loguru import logger as log
from multibajajmgt.common import get_dated_dir, get_files, mk_dir, write_to_json
from multibajajmgt.config import INVOICE_DIR, INVOICE_HISTORY_DIR
from multibajajmgt.enums import (
    BasicFieldName as Field,
    DocumentResourceExtension as DocExt,
    DPMCFieldName as DPMCField,
    InvoiceField as InvoField,
    InvoiceStatus as Status
)
from multibajajmgt.exceptions import DataNotFoundError

curr_historical_dir = get_dated_dir(INVOICE_HISTORY_DIR)


def _reindex_df(df, index):
    """ Reindex and remove nan values by empty string.

    :param df: pandas dataframe,
    :param index: list, columns for reindex.
    :return: pandas dataframe, restructured dataframe.
    """
    return df \
        .reindex(index, axis = "columns") \
        .fillna("")


def _fetch_advanced_data(invoice_type, invoice_id):
    """ Setup and Fetch data accordingly to passed parameters.

    :param invoice_type: str, Could be Invoice/Mobile/Order.
    :param invoice_id: str, identification.
    :return: dict, fetched data.
    """
    # Setup payload fields depending on available info in base file
    col_name = "STR_INVOICE_NO"
    # Fetch invoice data(invoice and GRN numbers) from DPMC server
    try:
        if "Order" in invoice_type:
            col_name = "STR_DLR_ORD_NO"
        elif "Mobile" in invoice_type:
            col_name = "STR_MOBILE_INVOICE_NO"
        data = dpmc_client.inquire_goodreceivenote_by_order_ref(col_name, invoice_id)
    except DataNotFoundError:
        try:
            # Usually used for older invoices, since "inquire_goodreceivenote_by_order_ref"'s data expires fast
            if "Order" in invoice_type:
                col_name = "STR_ORDER_NO"
            elif "Mobile" in invoice_type:
                # Mobile invoice ID fetch no longer works
                log.warning("Failed to retrieve Invoice: {}, Mobile Invoice ID expired.", invoice_id)
                return
            data = dpmc_client.inquire_goodreceivenote_by_grn_ref(col_name, invoice_id)
        except DataNotFoundError:
            log.warning("Failed to retrieve Invoice: {}.", invoice_id)
            return
    return data


def _enrich_with_advanced_data(row):
    """ Enrich invoices with grn and order id.

    :param row: pandas series, rows of a dataframe.
    :return: pandas series, enriched row.
    """
    # Can-be invoice, order, mobile number
    default_id = row[InvoField.default_id]
    # Configure and get data
    invoice_data = _fetch_advanced_data(row[InvoField.type], default_id)
    # If getting data didn't work properly
    if not invoice_data:
        row[Field.status] = Status.failed
        return row
    if len(invoice_data) > 1:
        # If "id" is incomplete and matches parts of multiple invoice ids.
        row[Field.status] = Status.multiple
        row[InvoField.default_id] = [invoice_data[n][DPMCField.invoice_no.order] for n in range(len(invoice_data))]
    else:
        invoice_data = invoice_data[0]
        row[Field.status] = Status.success
        # common for both requests
        row[InvoField.default_id] = invoice_data[DPMCField.invoice_no.order]
        row[InvoField.order_id] = invoice_data[DPMCField.order_no.order]
        if DPMCField.grn_no.grn in invoice_data:
            # Unique to "inquire_goodreceivenote_by_grn_ref"
            row[InvoField.grn_id] = invoice_data[DPMCField.grn_no.grn]
        else:
            # Unique to "inquire_goodreceivenote_by_order_ref"
            row[InvoField.mobile_id] = invoice_data[DPMCField.mobile_no.order]
    log.success("Retrieved Invoice: {}.", default_id)
    return row


def export_invoice_data():
    """ Fetch, enrich and restructure DPMC invoices with advanced data.
    """
    log.info("Export DPMC Invoice data.")
    invoice_file = f"{get_files().get_invoice()}.{DocExt.json}"
    historical_file = mk_dir(curr_historical_dir, invoice_file)
    invoice_df = pd.read_json(f"{INVOICE_DIR}/{invoice_file}", orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_advanced_data, axis = 1)
    # Restructure dataframe by reordering and deleting columns
    invoice_df = _reindex_df(invoice_df, [InvoField.date, Field.status, InvoField.type, InvoField.default_id,
                                          InvoField.order_id, InvoField.mobile_id, InvoField.grn_id])
    write_to_json(historical_file, invoice_df.to_dict("records"))


def _reformat_product_data(grn_id, product_data):
    """ Setup drop and rename attributes of each product.

    A condition(`if grn_id`) is necessary ,since there are 2 client functions to get product data.
    Each returning a different payload.

    :param grn_id: string | None, if string `..._by_grn_ref` is used else `..._by_order_ref` is used.
    :param product_data: list of dicts, data.
    :return: list of dicts, changed data.
    """
    products = product_data[DPMCField.grn_detail.order]["Table"] if grn_id else product_data[DPMCField.grn_detail.grn]
    product_df = pd.DataFrame(products)
    if grn_id:
        product_df = product_df \
            .drop([DPMCField.ware_code.grn,
                   DPMCField.loc_code.grn,
                   DPMCField.rack_code.grn,
                   DPMCField.bin_code.grn,
                   DPMCField.sbin_code.grn,
                   DPMCField.serial_base.grn], axis = 1) \
            .rename(columns = {DPMCField.part_code.grn: InvoField.part_code,
                               DPMCField.part_desc.grn: InvoField.part_desc,
                               DPMCField.part_qty.grn: InvoField.part_qty,
                               DPMCField.unit_cost.grn: InvoField.unit_cost,
                               DPMCField.total.grn: InvoField.total})
    else:
        product_df = product_df \
            .drop([DPMCField.ware_code.order,
                   DPMCField.serial_base.order], axis = 1) \
            .rename(columns = {DPMCField.part_code.order: InvoField.part_code,
                               DPMCField.part_desc.order: InvoField.part_desc,
                               DPMCField.part_qty.order: InvoField.part_qty,
                               DPMCField.unit_cost.order: InvoField.unit_cost,
                               DPMCField.total.order: InvoField.total})
    products = product_df.to_dict("records")
    return products


def _enrich_with_products(row):
    """ Enrich invoices with the products.

    :param row: pandas series, rows of a dataframe.
    :return: pandas series, enriched row.
    """
    invoice_status = row[Field.status]
    invoice_id = row[InvoField.default_id]
    grn_id = row[InvoField.grn_id]
    # Filter invoices unsuccessful with fetching advanced data
    if Status.success in invoice_status:
        try:
            product_data = dpmc_client.inquire_products_by_invoice(invoice_id, grn_id)
        except DataNotFoundError:
            log.warning("Failed to retrieve Invoice: {} products.", invoice_id)
            row[Field.status] = Status.failed
            return row
        log.success("Retrieved Invoice {} products.", invoice_id)
        row[InvoField.products] = _reformat_product_data(grn_id, product_data)
    return row


def export_products():
    """ Fetch and enrich invoices with products.
    """
    log.info("Export DPMC Invoice products.")
    historical_file = mk_dir(curr_historical_dir, f"{get_files().get_invoice()}.{DocExt.json}")
    invoice_df = pd.read_json(historical_file, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_products, axis = 1)
    invoice_df = _reindex_df(invoice_df, [InvoField.date, Field.status, InvoField.type, InvoField.default_id,
                                          InvoField.order_id, InvoField.mobile_id, InvoField.grn_id,
                                          InvoField.products])
    write_to_json(historical_file, invoice_df.to_dict("records"))
