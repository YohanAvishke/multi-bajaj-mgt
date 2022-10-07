import logging

import multibajajmgt.clients.dpmc.client as dpmc_client
import pandas as pd

from multibajajmgt.common import write_to_json, mk_historical, get_curr_dir, get_now_file
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


def fetch_invoices():
    invoices = pd.read_json(BASE_FILE, orient = "records").Adjustments.to_list()
    for invoice in invoices:
        invoice_type = invoice[JSONField.type]
        # Could be invoice, order, mobile number
        default_id = invoice[JSONField.default_id]
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
            except DataNotFoundError as e:
                log.error(f"Invoice retrieval failed for {default_id} of {invoice_type}", e)
                invoice[JSONField.status] = Status.failed
                continue
        if len(invoice_data) > 1:
            # If "id" is incomplete and matches parts of multiple invoice ids.
            invoice[JSONField.status] = Status.multiple
            invoice[JSONField.invoice_id] = [invoice_data[n]["Invoice No"] for n in range(len(invoice_data))]
        else:
            invoice_data = invoice_data[0]
            invoice[JSONField.status] = Status.success
            invoice[JSONField.invoice_id] = invoice_data["Invoice No"]
            # Available after a call to "inquire_goodreceivenote_by_grn_ref"
            if "GRN No" in invoice_data:
                invoice[JSONField.grn_id] = invoice_data["GRN No"]
            if "Order No" in invoice_data:
                invoice[JSONField.order_id] = invoice_data["Order No"]
        log.info(f"Invoice retrieved success for {default_id} of {invoice_type}")
        # Remove default data
        del invoice[JSONField.default_id]
    # Save fetched data
    adjustments = {JSONField.invoices: invoices}
    historical_file_path = mk_historical(get_curr_dir(HISTORY_DIR), DocumentResourceType.invoice_dpmc)
    write_to_json(historical_file_path, adjustments)
