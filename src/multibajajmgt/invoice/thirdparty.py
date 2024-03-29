import pandas as pd

from loguru import logger as log
from multibajajmgt.common import get_dated_dir, get_files, mk_dir, write_to_json
from multibajajmgt.config import INVOICE_DIR, INVOICE_HISTORY_DIR
from multibajajmgt.enums import (
    BasicFieldName as BaseField,
    DocumentResourceExtension as DocExt,
    InvoiceField as InvoField,
    InvoiceStatus as Status
)

curr_historical_dir = get_dated_dir(INVOICE_HISTORY_DIR)


def _breakdown_invoices(invoice_df):
    """ Identify and break raw data into separate invoices.

    Each invoice is identified by the `*` char. Which should be in the 0the index of a row's data.

    :param invoice_df: pandas dataframe, raw data.
    :return: list, broken down invoices.
    """
    invoice_indexes = invoice_df.query("Invoices.str.contains('\\*')").index.values.tolist()
    boundaries = invoice_indexes + [len(invoice_df.index)]
    invoices = [(invoice_df.iloc[boundaries[n]:boundaries[n + 1]]) for n in range(len(boundaries) - 1)]
    return invoices


def _enrich_invoices(invoices):
    """ Get basic invoice data and product data, extracted from raw data.

    :param invoices: list, raw data.
    :return: list, enriched data.
    """
    enriched_invoices = []
    for invoice_df in invoices:
        invoice_df.reset_index(drop = True, inplace = True)
        # First row always contains invoice
        info = invoice_df.loc[0].values.all()
        # Break invoice data into groups
        info = info.split("*")[-1].split("&")
        invo_id = info[0]
        # Break product data into separate lists
        raw_df = invoice_df[1:].apply(lambda x: x.Invoices.split(" "), axis = 1)
        # Skip the rest if no products are available in the invoice
        if len(raw_df) == 0:
            log.warning("Failed to enrich Invoice: {} products. None found.", invo_id)
            continue
        names = raw_df.apply(lambda x: str(" ".join(x[3:]))).to_list()
        codes = raw_df.apply(lambda x: x[0]).to_list()
        quantities = raw_df.apply(lambda x: int(x[1])).to_list()
        costs = raw_df.apply(lambda x: float(x[2])).to_list()
        # Create dict from all the product data lists
        products = [
            {InvoField.part_code: code, InvoField.part_desc: name, InvoField.part_qty: quantity,
             InvoField.unit_cost: cost}
            for code, name, quantity, cost in zip(codes, names, quantities, costs)
        ]
        # Setup enriched invoice
        invoice = {
            InvoField.date: info[-1],
            BaseField.status: Status.success,
            InvoField.default_id: invo_id,
            InvoField.products: products
        }
        enriched_invoices.append(invoice)
        log.success("Enriched Invoice: {}.", invo_id)
    return enriched_invoices


def export_invoice_data():
    """ Get raw invoice data, convert and save it in a historical file.
    """
    log.info("Export ThirdParty Invoice.")
    historical_file = mk_dir(curr_historical_dir, f"{get_files().get_invoice()}.{DocExt.json}")
    invoice_df = pd.read_csv(f"{INVOICE_DIR}/{get_files().get_invoice()}.{DocExt.txt}", header = None,
                             names = ["Invoices"])
    # Find and break each invoice into a different object
    invoices = _breakdown_invoices(invoice_df)
    # Enrich invoices with advance data and product data
    enriched_invoices = _enrich_invoices(invoices)
    write_to_json(historical_file, enriched_invoices)
