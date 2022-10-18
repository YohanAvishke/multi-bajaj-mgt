import logging

import multibajajmgt.clients.googlesheet.client as sale_client
import pandas as pd

from multibajajmgt.common import *
from multibajajmgt.config import INVOICE_HISTORY_DIR
from multibajajmgt.enums import (
    BasicFieldName as Field,
    DocumentResourceName as DRName,
    DocumentResourceExtension as DRExt,
    InvoiceStatus as Status,
)

log = logging.getLogger(__name__)
curr_historical_dir = get_dated_dir(INVOICE_HISTORY_DIR)


def fetch_invoice_data():
    historical_file = mk_dir(curr_historical_dir, f"{DRName.invoice_sales}.{DRExt.json}")
    invoices = []
    enriched_invoices = []
    data = sale_client.fetch_sheet_data()
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
    # Combine all chunks to a single invoice dataframe
    for chunk in chunks:
        invoices.append(pd.DataFrame(chunk))
    chunk_df = pd.concat(invoices, ignore_index = True)
    # Break invoices to be enriched by advance data
    invoice_indexes = chunk_df.query(f"{Field.date} == {Field.date}").index.values.tolist()
    boundaries = invoice_indexes + [len(chunk_df.index)]
    invoices = [(chunk_df.iloc[boundaries[n]:boundaries[n + 1]]) for n in range(len(boundaries) - 1)]
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
        write_to_json(historical_file, enriched_invoices)
