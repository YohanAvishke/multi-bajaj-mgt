import logging

import multibajajmgt.clients.dpmc.client as dpmc_client
import pandas as pd

from multibajajmgt.common import *
from multibajajmgt.config import INVOICE_BASE_FILE, INVOICE_HISTORY_DIR
from multibajajmgt.enums import (
    InvoiceJSONFieldName as JSONField,
    InvoiceStatus as Status,
    InvoiceType as Type,
    DocumentResourceType as DSType,
    DocumentResourceExtension as DSExt,
    DPMCFieldName as Field
)
from multibajajmgt.exceptions import DataNotFoundError

log = logging.getLogger(__name__)
historical_dir = get_curr_dir(INVOICE_HISTORY_DIR)
historical_base_file = mk_historical(historical_dir, get_now_file({DSExt.json}, {DSType.invoice_dpmc}))


def get_h_dir():
    """ Return curr_date dir

    :return: string, dir path
    """
    return historical_dir


def get_h_file():
    """ Return "invoice_dpmc.json" in curr_date dir

    :return: string, file path
    """
    return historical_base_file


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
    # For column types used in the request
    order_field = grn_field = None
    # Setup payload fields depending on available info in base file
    if Type.invoice in invoice_type:
        order_field = grn_field = Field.invoice_no
    elif Type.order in invoice_type:
        order_field = Field.dlr_order_no
        grn_field = Field.order_no
    elif Type.mobile in invoice_type:
        order_field = Field.mobile_no
    # Fetch invoice data(invoice and GRN numbers) from DPMC server
    try:
        invoice_data = dpmc_client.inquire_goodreceivenote_by_order_ref(order_field, default_id)
    except DataNotFoundError:
        try:
            # Usually happens when for older invoices since "inquire_goodreceivenote_by_order_ref"'s data expires
            # fast
            invoice_data = dpmc_client.inquire_goodreceivenote_by_grn_ref(grn_field, default_id)
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
    invoice_df = pd.read_json(INVOICE_BASE_FILE, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_advanced_data, axis = 1)
    # Restructure dataframe by reordering and deleting columns
    invoice_df = invoice_df \
        .drop(JSONField.default_id, axis = 1)
    invoice_df = _reindex_df(invoice_df, [JSONField.date, JSONField.status, JSONField.type, JSONField.invoice_id,
                                          JSONField.order_id, JSONField.grn_id])
    write_to_json(get_h_file(), invoice_df.to_dict("records"))


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
        # If grn id is used to fetch data payload will be different
        products = product_data["dsGRNDetails"]["Table"] if grn_id else product_data["dtGRNDetails"]
        # Restructure dataframe by dropping unused columns and rename the rest
        products = pd \
            .DataFrame(products) \
            .drop([Field.ware_code, Field.loc_code, Field.rack_code, Field.bin_code, Field.sbin_code,
                   Field.serial_base], axis = 1) \
            .rename(columns = {Field.part_code: JSONField.part_code, Field.part_desc: JSONField.part_desc,
                               Field.part_qty: JSONField.part_qty, Field.unit_cost: JSONField.unit_cost,
                               Field.total: JSONField.total}) \
            .to_dict("records")
        row[JSONField.products] = products
        logging.info(f"Product inquiry success for Invoice {invoice_id}")
    return row


def fetch_products():
    """ Fetch and enrich invoices with products.
    """
    file = get_h_file()
    invoice_df = pd.read_json(file, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_products, axis = 1)
    invoice_df = _reindex_df(invoice_df, [JSONField.date, JSONField.status, JSONField.type, JSONField.invoice_id,
                                          JSONField.order_id, JSONField.grn_id, JSONField.products])
    write_to_json(file, invoice_df.to_dict("records"))
