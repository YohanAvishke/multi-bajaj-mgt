import logging

import multibajajmgt.clients.dpmc.client as dpmc_client
import pandas as pd

from multibajajmgt.common import *
from multibajajmgt.config import INVOICE_BASE_FILE, INVOICE_HISTORY_DIR
from multibajajmgt.enums import (
    InvoiceJSONFieldName as JSONField,
    InvoiceStatus as Status,
    InvoiceType as Type,
    DocumentResourceType as DRType,
    DocumentResourceExtension as DRExt,
    DPMCFieldName as Field
)
from multibajajmgt.exceptions import DataNotFoundError

log = logging.getLogger(__name__)
curr_historical_dir = get_dated_dir(INVOICE_HISTORY_DIR)


def _reindex_df(df, index):
    """ Reindex and remove nan values by empty string.

    :param df: pandas dataframe,
    :param index: list, columns for reindex
    :return: pandas dataframe, restructured dataframe
    """
    return df \
        .reindex(index, axis = "columns") \
        .fillna("")


def _enrich_with_advanced_data(row):
    """ Enrich invoices with grn and order id.

    :param row: pandas series, rows of a dataframe
    :return: pandas series, enriched row
    """
    invoice_type = row[JSONField.type]
    # Can-be invoice, order, mobile number
    default_id = row[JSONField.default_id]
    # For column name used in the request
    col_name = None
    # Setup payload fields depending on available info in base file
    # Incase Type.order is necessary which is not used currently
    #   if Type.order in "Order":
    #       order_field = "STR_DLR_ORD_NO"
    #       grn_field = "STR_ORDER_NO"
    if Type.invoice.val in invoice_type:
        col_name = Type.invoice.col
    elif Type.mobile.val in invoice_type:
        col_name = Type.mobile.col
    # Fetch invoice data(invoice and GRN numbers) from DPMC server
    try:
        invoice_data = dpmc_client.inquire_goodreceivenote_by_order_ref(col_name, default_id)
    except DataNotFoundError:
        try:
            # Usually happens for older invoices, since "inquire_goodreceivenote_by_order_ref"'s data expires fast
            invoice_data = dpmc_client.inquire_goodreceivenote_by_grn_ref(col_name, default_id)
        except DataNotFoundError:
            log.error(f"Invoice retrieval failed for {default_id}")
            row[JSONField.status] = Status.failed
            return row
    if len(invoice_data) > 1:
        # If "id" is incomplete and matches parts of multiple invoice ids.
        row[JSONField.status] = Status.multiple
        row[JSONField.invoice_id] = [invoice_data[n]["Invoice No"] for n in range(len(invoice_data))]
    else:
        invoice_data = invoice_data[0]
        row[JSONField.status] = Status.success
        row[JSONField.invoice_id] = invoice_data["Invoice No"]
        # Available after a call to "inquire_goodreceivenote_by_grn_ref"
        if "GRN No" in invoice_data:
            row[JSONField.grn_id] = invoice_data["GRN No"]
        if "Order No" in invoice_data:
            row[JSONField.order_id] = invoice_data["Order No"]
    log.info(f"Invoice retrieval success for {default_id}")
    return row


def fetch_invoice_data():
    """ Fetch, enrich and restructure invoices with advanced data.
    """
    historical_file = mk_dir(curr_historical_dir, f"{DRType.invoice_dpmc}.{DRExt.json}")
    invoice_df = pd.read_json(INVOICE_BASE_FILE, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_advanced_data, axis = 1)
    # Restructure dataframe by reordering and deleting columns
    invoice_df = invoice_df \
        .drop(JSONField.default_id, axis = 1)
    invoice_df = _reindex_df(invoice_df, [JSONField.date, JSONField.status, JSONField.type, JSONField.invoice_id,
                                          JSONField.order_id, JSONField.grn_id])
    write_to_json(historical_file, invoice_df.to_dict("records"))


def _reformat_product_data(grn_id, product_data):
    """ Setup drop and rename attributes of each product.

    A condition(`if grn_id`) is necessary ,since there are 2 client functions to get product data.
    Each returning a different payload.

    :param grn_id: string | None, if string `..._by_grn_ref` is used else `..._by_order_ref` is used
    :param product_data: list of dicts, data
    :return: list of dicts, changed data
    """
    products = product_data["dsGRNDetails"]["Table"] if grn_id else product_data["dtGRNDetails"]
    product_df = pd.DataFrame(products)
    if grn_id:
        product_df = product_df \
            .drop([Field.ware_code.grn,
                   Field.loc_code.grn,
                   Field.rack_code.grn,
                   Field.bin_code.grn,
                   Field.sbin_code.grn,
                   Field.serial_base.grn], axis = 1) \
            .rename(columns = {Field.part_code.grn: JSONField.part_code,
                               Field.part_desc.grn: JSONField.part_desc,
                               Field.part_qty.grn: JSONField.part_qty,
                               Field.unit_cost.grn: JSONField.unit_cost,
                               Field.total.grn: JSONField.total})
    else:
        product_df = product_df \
            .drop([Field.ware_code.order,
                   Field.serial_base.order], axis = 1) \
            .rename(columns = {Field.part_code.order: JSONField.part_code,
                               Field.part_desc.order: JSONField.part_desc,
                               Field.part_qty.order: JSONField.part_qty,
                               Field.unit_cost.order: JSONField.unit_cost,
                               Field.total.order: JSONField.total})
    products = product_df.to_dict("records")
    return products


def _enrich_with_products(row):
    """ Enrich invoices with the products.

    :param row: pandas series, rows of a dataframe
    :return: pandas series, enriched row
    """
    invoice_status = row[JSONField.status]
    invoice_id = row[JSONField.invoice_id]
    grn_id = row[JSONField.grn_id]
    # Filter invoices unsuccessful with fetching advanced data
    if Status.success in invoice_status:
        try:
            product_data = dpmc_client.inquire_product_by_invoice(invoice_id, grn_id)
        except DataNotFoundError:
            log.error(f"Product inquiry failed for Invoice {invoice_id}")
            row[JSONField.status] = Status.failed
            return row
        row[JSONField.products] = _reformat_product_data(grn_id, product_data)
        logging.info(f"Product inquiry success for Invoice {invoice_id}")
    return row


def fetch_products():
    """ Fetch and enrich invoices with products.
    """
    historical_file = mk_dir(curr_historical_dir, f"{DRType.invoice_dpmc}.{DRExt.json}")
    invoice_df = pd.read_json(historical_file, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_products, axis = 1)
    invoice_df = _reindex_df(invoice_df, [JSONField.date, JSONField.status, JSONField.type, JSONField.invoice_id,
                                          JSONField.order_id, JSONField.grn_id, JSONField.products])
    write_to_json(historical_file, invoice_df.to_dict("records"))
