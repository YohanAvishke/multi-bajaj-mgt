import logging

import multibajajmgt.clients.dpmc.client as dpmc_client
import pandas as pd

from multibajajmgt.common import *
from multibajajmgt.config import DATA_DIR
from multibajajmgt.enums import (
    InvoiceJSONFieldName as JSONField,
    InvoiceStatus as Status,
    InvoiceType as Type,
    DocumentResourceType,
    DPMCFieldName as Field
)
from multibajajmgt.exceptions import DataNotFoundError

log = logging.getLogger(__name__)

BASE_FILE = f"{DATA_DIR}/invoice/{DocumentResourceType.invoice_dpmc}"
HISTORY_DIR = f"{DATA_DIR}/invoice/history"
REINDEX_LIST = [JSONField.date, JSONField.status, JSONField.type, JSONField.invoice_id, JSONField.order_id,
                JSONField.grn_id, JSONField.products]


def _enrich_with_metadata(row):
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


def fetch_invoice_metadata():
    invoice_df = pd.read_json(BASE_FILE, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_metadata, axis = 1)
    historical_file = mk_historical(get_curr_dir(HISTORY_DIR), DocumentResourceType.invoice_dpmc)
    invoice_df = invoice_df \
        .drop(JSONField.default_id, axis = 1)
    invoice_df = restructure_df(invoice_df, REINDEX_LIST)
    write_to_json(historical_file, invoice_df.to_dict("records"))


def _enrich_with_products(row):
    invoice_status = row[JSONField.status]
    invoice_id = row[JSONField.invoice_id]
    grn_id = row[JSONField.grn_id]
    if Status.success in invoice_status:
        try:
            product_data = dpmc_client.inquire_product_by_invoice(invoice_id, grn_id)
        except DataNotFoundError:
            log.error(f"Product inquiry failed for Invoice {invoice_id}")
            row[JSONField.status] = Status.failed
            return row
        products = product_data["dsGRNDetails"]["Table"] if grn_id else product_data["dtGRNDetails"]
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
    historical_file = mk_historical(get_curr_dir(HISTORY_DIR), DocumentResourceType.invoice_dpmc)
    invoice_df = pd.read_json(historical_file, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_products, axis = 1)
    invoice_df = restructure_df(invoice_df, REINDEX_LIST)
    write_to_json(historical_file, invoice_df.to_dict("records"))
