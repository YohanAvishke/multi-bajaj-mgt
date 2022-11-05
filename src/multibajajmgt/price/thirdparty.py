import itertools
import pandas as pd
import multibajajmgt.client.odoo.client as odoo_client

from multibajajmgt.common import csvstr_to_df, get_dated_dir, get_now_file, mk_dir, write_to_csv
from multibajajmgt.config import INVOICE_HISTORY_DIR, PRICE_BASE_TP_FILE, PRICE_HISTORY_DIR
from multibajajmgt.enums import (
    BasicFieldName as Basic,
    DocumentResourceName as DRName,
    DocumentResourceExtension as DRExt,
    InvoiceStatus as InvoStatus,
    InvoiceField as InvoField,
    OdooFieldLabel as OdooLabel,
    ProductPriceStatus as PriceStatus
)

curr_invoice_dir = get_dated_dir(INVOICE_HISTORY_DIR)
curr_his_dir = get_dated_dir(PRICE_HISTORY_DIR)


def export_prices():
    raw_price = odoo_client.fetch_all_thirdparty_prices()
    price_df = csvstr_to_df(raw_price)
    write_to_csv(PRICE_BASE_TP_FILE, price_df)


def _extract_invoice_products():
    invoices_df = pd.read_json(f"{curr_invoice_dir}/{DRName.invoice_tp}.{DRExt.json}", convert_dates = False)
    invoices_df = invoices_df[invoices_df[Basic.status] == InvoStatus.success]
    chunks = [row.Products for row in invoices_df.itertuples()]
    products = list(itertools.chain.from_iterable(chunks))
    products_df = pd.DataFrame(products).drop(["Name", "Quantity"], axis = 1)
    return products_df


def _enrich_product_prices(price_df, products_df):
    df = products_df.merge(price_df, how = "left", indicator = Basic.found_in, left_on = InvoField.part_code,
                           right_on = OdooLabel.internal_id)
    df = df[df[Basic.found_in] == "both"]
    return df


def _calculate_status(row):
    price = row["Unit Cost"]
    old_price = row["Old Sales Price"]
    if price > old_price:
        status = PriceStatus.up
    elif price < old_price:
        status = PriceStatus.down
    else:
        status = PriceStatus.equal
    row["Status"] = status
    return row


def update_product_prices():
    historical_file_path = mk_dir(curr_his_dir, f"{DRName.price_tp}.{DRExt.csv}")
    price_df = pd.read_csv(PRICE_BASE_TP_FILE)
    products_df = _extract_invoice_products()
    enriched_df = _enrich_product_prices(price_df, products_df)
    enriched_df = enriched_df.apply(_calculate_status, axis = 1)
    write_to_csv(historical_file_path, enriched_df,
                 columns = ["External ID", "Internal Reference", "Old Sales Price", "Old Cost", "Unit Cost",
                            "Unit Cost", "Status"],
                 header = ["External ID", "Internal Reference", "Old Sales Price", "Old Cost", "Sales Price",
                           "Cost", "Status"])
