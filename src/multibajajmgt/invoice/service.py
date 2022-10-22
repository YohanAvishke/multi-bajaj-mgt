import logging

import multibajajmgt.clients.dpmc.client as dpmc_client
import multibajajmgt.clients.googlesheet.client as sale_client
import pandas as pd

from multibajajmgt.common import *
from multibajajmgt.config import INVOICE_DPMC_FILE, INVOICE_HISTORY_DIR
from multibajajmgt.enums import (
    BasicFieldName as Field,
    DocumentResourceName as DRName,
    DocumentResourceExtension as DRExt,
    DPMCFieldName as DPMCField,
    InvoiceStatus as Status,
    InvoiceType as Type
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
    invoice_type = row[Field.type]
    # Can-be invoice, order, mobile number
    default_id = row[Field.default_id]
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
            row[Field.status] = Status.failed
            return row
    if len(invoice_data) > 1:
        # If "id" is incomplete and matches parts of multiple invoice ids.
        row[Field.status] = Status.multiple
        row[Field.default_id] = [invoice_data[n][DPMCField.invoice_no.order] for n in range(len(invoice_data))]
    else:
        invoice_data = invoice_data[0]
        row[Field.status] = Status.success
        # common for both requests
        row[Field.default_id] = invoice_data[DPMCField.invoice_no.order]
        row[Field.order_id] = invoice_data[DPMCField.order_no.order]
        if DPMCField.grn_no.grn in invoice_data:
            # Unique to "inquire_goodreceivenote_by_grn_ref"
            row[Field.grn_id] = invoice_data[DPMCField.grn_no.grn]
        else:
            # Unique to "inquire_goodreceivenote_by_order_ref"
            row[Field.mobile_id] = invoice_data[DPMCField.mobile_no.order]
    log.info(f"Invoice retrieval success for {default_id}")
    return row


def export_dpmc_invoice_data():
    """ Fetch, enrich and restructure DPMC invoices with advanced data.
    """
    historical_file = mk_dir(curr_historical_dir, f"{DRName.invoice_dpmc}.{DRExt.json}")
    invoice_df = pd.read_json(INVOICE_DPMC_FILE, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_advanced_data, axis = 1)
    # Restructure dataframe by reordering and deleting columns
    invoice_df = _reindex_df(invoice_df, [Field.date, Field.status, Field.type, Field.default_id,
                                          Field.order_id, Field.mobile_id, Field.grn_id])
    write_to_json(historical_file, invoice_df.to_dict("records"))


def _extract_chunks(data):
    """ Extract chunks from raw data.

    Chunks are rows with `STR_PART_NO	INT_QUATITY	DATE	False`.

    :param data: dict, raw data
    :return: pandas dataframe, identified chunks
    """
    chunk_df_list = []
    # Indexes of the rows containing the column names
    chunk_indexes = data.query(f"{Field.status} == 'False'").index.values.tolist()
    # [column indexes] +  index of last product in invoice
    boundaries = chunk_indexes + [len(data.index)]
    # Get all data inbetween indexes(including the index)
    chunks = [(data.iloc[(boundaries[n] + 1):boundaries[n + 1]]) for n in range(len(boundaries) - 1)]
    chunks = [chunks[n]
              .apply(lambda x: x.str.strip())  # Remove all whitespaces
              .drop(columns = [Field.status])
              .to_dict("records")
              for n in range(len(chunks))]
    # Combine all chunks to a single dataframe
    for chunk in chunks:
        chunk_df_list.append(pd.DataFrame(chunk))
    chunks_df = pd.concat(chunk_df_list, ignore_index = True)
    return chunks_df


def _extract_invoices(chunks_df):
    """ Extract invoices from chunks.

    Invoices are rows with value attached to column `DATE`. Representing sales of each day.

    :param chunks_df: pandas dataframe, chunks from `_extract_chunks`
    :return: list of dicts, savable invoices
    """
    enriched_invoices = []
    # Identify invoices(rows with value to date)
    invoice_indexes = chunks_df.query(f"{Field.date} == {Field.date}").index.values.tolist()
    boundaries = invoice_indexes + [len(chunks_df.index)]
    invoices = [(chunks_df.iloc[boundaries[n]:boundaries[n + 1]]) for n in range(len(boundaries) - 1)]
    # Enrich invoices
    for invoice_df in invoices:
        invoice_df.reset_index(drop = True, inplace = True)
        date = invoice_df[Field.date][0]
        products = invoice_df[[Field.part_code, Field.part_qty]].to_dict('records')
        invoice = {
            Field.date: date,
            Field.status: Status.success,
            Field.default_id: f"Sales of {date}",
            Field.products: products,
        }
        enriched_invoices.append(invoice)
    return enriched_invoices


def export_sales_invoice_data():
    """ Fetch, enrich and restructure Sales invoices with advanced data.
    """
    historical_file = mk_dir(curr_historical_dir, f"{DRName.invoice_sales}.{DRExt.json}")
    data = sale_client.inquire_sales_invoices()
    # Identify chunks(rows with a value to col `isUpdated`) in the data
    chunks_df = _extract_chunks(data)
    enriched_invoices = _extract_invoices(chunks_df)
    write_to_json(historical_file, enriched_invoices)


def _reformat_product_data(grn_id, product_data):
    """ Setup drop and rename attributes of each product.

    A condition(`if grn_id`) is necessary ,since there are 2 client functions to get product data.
    Each returning a different payload.

    :param grn_id: string | None, if string `..._by_grn_ref` is used else `..._by_order_ref` is used
    :param product_data: list of dicts, data
    :return: list of dicts, changed data
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
            .rename(columns = {DPMCField.part_code.grn: Field.part_code,
                               DPMCField.part_desc.grn: Field.part_desc,
                               DPMCField.part_qty.grn: Field.part_qty,
                               DPMCField.unit_cost.grn: Field.unit_cost,
                               DPMCField.total.grn: Field.total})
    else:
        product_df = product_df \
            .drop([DPMCField.ware_code.order,
                   DPMCField.serial_base.order], axis = 1) \
            .rename(columns = {DPMCField.part_code.order: Field.part_code,
                               DPMCField.part_desc.order: Field.part_desc,
                               DPMCField.part_qty.order: Field.part_qty,
                               DPMCField.unit_cost.order: Field.unit_cost,
                               DPMCField.total.order: Field.total})
    products = product_df.to_dict("records")
    return products


def _enrich_with_products(row):
    """ Enrich invoices with the products.

    :param row: pandas series, rows of a dataframe
    :return: pandas series, enriched row
    """
    invoice_status = row[Field.status]
    invoice_id = row[Field.default_id]
    grn_id = row[Field.grn_id]
    # Filter invoices unsuccessful with fetching advanced data
    if Status.success in invoice_status:
        try:
            product_data = dpmc_client.inquire_product_by_invoice(invoice_id, grn_id)
        except DataNotFoundError:
            log.error(f"Product inquiry failed for Invoice {invoice_id}")
            row[Field.status] = Status.failed
            return row
        row[Field.products] = _reformat_product_data(grn_id, product_data)
        logging.info(f"Product inquiry success for Invoice {invoice_id}")
    return row


def export_products():
    """ Fetch and enrich invoices with products.
    """
    historical_file = mk_dir(curr_historical_dir, f"{DRName.invoice_dpmc}.{DRExt.json}")
    invoice_df = pd.read_json(historical_file, orient = "records", convert_dates = False)
    invoice_df = invoice_df.apply(_enrich_with_products, axis = 1)
    invoice_df = _reindex_df(invoice_df, [Field.date, Field.status, Field.type, Field.default_id,
                                          Field.order_id, Field.mobile_id, Field.grn_id, Field.products])
    write_to_json(historical_file, invoice_df.to_dict("records"))
