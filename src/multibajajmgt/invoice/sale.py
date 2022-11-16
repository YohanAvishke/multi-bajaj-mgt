import multibajajmgt.client.googlesheet.client as sale_client
import pandas as pd

from loguru import logger as log
from multibajajmgt.common import get_dated_dir, get_files, merge_duplicates, mk_dir, write_to_json
from multibajajmgt.config import INVOICE_HISTORY_DIR
from multibajajmgt.enums import (
    BasicFieldName as BaseField,
    DocumentResourceExtension as DocExt,
    InvoiceField as InvoField,
    InvoiceStatus as Status,
)

curr_historical_dir = get_dated_dir(INVOICE_HISTORY_DIR)


def _extract_chunks(data):
    """ Extract chunks from raw data.

    Chunks are rows with `STR_PART_NO  INT_QUATITY  DATE  False`.

    :param data: dict, raw data
    :return: pandas dataframe, identified chunks
    """
    chunk_df_list = []
    # Indexes of the rows containing the column names
    chunk_indexes = data.query(f"{BaseField.status} == 'False'").index.values.tolist()
    # [column indexes] +  index of last product in invoice
    boundaries = chunk_indexes + [len(data.index)]
    # Get all data inbetween indexes(including the index)
    chunks = [(data.iloc[(boundaries[n] + 1):boundaries[n + 1]]) for n in range(len(boundaries) - 1)]
    chunks = [chunks[n]
              .apply(lambda x: x.str.strip())  # Remove all whitespaces
              .drop(columns = [BaseField.status])
              .to_dict("records")
              for n in range(len(chunks))]
    # Combine all chunks to a single dataframe
    for chunk in chunks:
        chunk_df_list.append(pd.DataFrame(chunk))
    chunks_df = pd \
        .concat(chunk_df_list, ignore_index = True) \
        .astype({InvoField.part_qty: int})
    return chunks_df


def _extract_invoices(chunks_df):
    """ Extract invoices from chunks.

    Invoices are rows with value attached to column `DATE`. Representing sales of each day.

    :param chunks_df: pandas dataframe, chunks from `_extract_chunks`
    :return: list of dicts, savable invoices
    """
    enriched_invoices = []
    # Identify invoices(rows with value to date)
    invoice_indexes = chunks_df.query(f"{InvoField.date} == {InvoField.date}").index.values.tolist()
    boundaries = invoice_indexes + [len(chunks_df.index)]
    invoices = [(chunks_df.iloc[boundaries[n]:boundaries[n + 1]]) for n in range(len(boundaries) - 1)]
    # Enrich invoices
    for invoice_df in invoices:
        invoice_df.reset_index(drop = True, inplace = True)
        date = invoice_df[InvoField.date][0]
        products = invoice_df[[InvoField.part_code, InvoField.part_qty]].to_dict('records')
        invoice = {
            InvoField.date: date,
            BaseField.status: Status.success,
            InvoField.default_id: f"Sales of {date}",
            InvoField.products: products,
        }
        enriched_invoices.append(invoice)
    return enriched_invoices


def export_invoice_data():
    """ Fetch, enrich and restructure Sales invoices with advanced data.
    """
    log.info("Exporting sales invoices enriched by advanced data")
    historical_file = mk_dir(curr_historical_dir, f"{get_files().get_invoice()}.{DocExt.json}")
    data = sale_client.inquire_sales_invoices()
    # Identify chunks(rows with a value to col `isUpdated`) in the data
    chunks_df = _extract_chunks(data)
    enriched_invoices = _extract_invoices(chunks_df)
    write_to_json(historical_file, enriched_invoices)
