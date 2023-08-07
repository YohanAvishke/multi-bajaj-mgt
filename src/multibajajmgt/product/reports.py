import pandas as pd

from loguru import logger as log
from multibajajmgt.common import get_files, write_to_csv
from multibajajmgt.config import PRODUCT_DIR, STOCK_DIR, ADJUSTMENT_DIR, INVOICE_HISTORY_DIR
from multibajajmgt.enums import (
    DocumentResourceExtension as DocExt,
    DocumentResourceName as DocName,
    OdooFieldLabel as OdooLabel,
    ProductEnrichmentCategories as ProdEnrichCateg
)
from pathlib import Path


def enrich(*enrichments: ProdEnrichCateg):
    log.info(f"Enrich products from {enrichments}.")
    stock_df = pd.read_csv(f"{STOCK_DIR}/{get_files().get_stock()}.{DocExt.csv}")
    stock_df = stock_df.drop("Product/Product/ID", axis = 1)
    product_df = pd.read_csv(f"{PRODUCT_DIR}/{DocName.product_report}.{DocExt.csv}")
    enriched_df = product_df \
        .merge(stock_df, how = "left", on = OdooLabel.internal_id) \
        .rename(columns = {"Quantity_On_Hand": "Bajaj"})
    enriched_df["YL ref"] = enriched_df.apply(lambda x: f"{x[OdooLabel.internal_id]}(YL)", axis = 1)
    enriched_df = enriched_df.merge(stock_df, how = "left", left_on = "YL ref", right_on = OdooLabel.internal_id)
    enriched_df = enriched_df \
        .rename(columns = {"Internal Reference_x": "Internal Reference", "Quantity_On_Hand": "YL"}) \
        .drop(["YL ref", "Internal Reference_y"], axis = 1) \
        .fillna(0)
    write_to_csv(f"{PRODUCT_DIR}/{DocName.product_report}.{DocExt.csv}", enriched_df)


def _get_adjustment_history():
    invalid_files = [
        "adjustment-21:04:29,30.csv",
        "adjustment-21:05:12.csv",
        "adjustment-21:05:18.csv",
        "adjustment-21:05:18-part:02.csv",
        "adjustment-21:05:21-sales.csv",
        "adjustment-21-04-21.csv",
        "adjustment-21-04-30.csv",
        "adjustment-21-05-01.csv",
        "adjustment-21-05-02.csv",
        "adjustment-2021-06-20.csv",
        "adjustment-2021-06-22.csv"
    ]
    # Read all adjustments except the ones in invalid_files
    files = sorted(Path(ADJUSTMENT_DIR).rglob("*.csv"))
    files = [f for f in files if f.name not in invalid_files]
    # Create the Dataframe
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index = True)
    # Drop unwanted columns
    df.drop([
        "Include Exhausted Products",
        "line_ids/product_id/id",
        "line_ids/location_id/id",
        "line_ids/product_qty",
        "line_ids / product_id / id",
        "line_ids / location_id / id",
        "line_ids / product_qty"
    ], axis = 1, inplace = True)
    # Duplicate invoice names
    cols = ["name", "Accounting Date"]
    df.loc[:, cols] = df.loc[:, cols].ffill()
    # Extract DPMC invoices
    df.query("name.str.contains('PRI') or name.str.contains('MIN')", inplace = True)
    df.reset_index(drop = True, inplace = True)
    # Formate Invoice Reference column
    df["name"] = df["name"].str.extract(r"(PRI\w+|MIN\w+)")
    # Formate Accounting Date column
    df["Accounting Date"] = df["Accounting Date"].str.replace("/", "-")
    # Merge all product-number columns into one
    df.fillna("", inplace = True)
    df["Product Number"] = df[["reference", "product_id", "InternalReference"]].sum(axis = 1)
    # Finalise the dataframe
    df.drop_duplicates(inplace = True)
    df.drop([
        "reference", "product_id", "InternalReference"
    ], axis = 1, inplace = True)
    df.rename(columns = {
        "name": "Invoice",
        "Accounting Date": "Date"
    }, inplace = True)
    return df


def _extract_product_df(row):
    try:
        # Create product columns
        df = pd.json_normalize(row.Products)
        df = df.assign(**{"Invoice": row.ID, "Date": row.Date})
        # Finalise dataframe
        df.rename(columns = {"ID": "Product Number", "Unit Cost": "Cost"}, inplace = True)
        return df
    except Exception as e:
        log.warning("Failed to extract products of: {}, due to: {}", row.ID, e)
        return pd.DataFrame()


def _get_cost_history():
    # Read all invoices
    files = sorted(Path(INVOICE_HISTORY_DIR).rglob("*_dpmc.json"))
    # Create the Dataframe
    df = pd.concat(
        (
            pd.read_json(f, convert_dates = False) for f in files
        ),
        ignore_index = True)
    # Filter successful invoices
    df.query("Status == 'Success'", inplace = True)
    # Merge duplicates and Sort
    df = df.groupby(["Date", "ID"], as_index = False).sum()
    df.sort_values(by = ["Date", "ID"], inplace = True)
    # Extract products into a Dataframe from the Column
    df = pd.concat([_extract_product_df(row) for row in df.itertuples()], ignore_index = True)
    # Finalise the dataframe
    df.drop(
        ["Name", "Quantity", "Total", "Date"],
        axis = 1, inplace = True)
    df.drop_duplicates(inplace = True)
    return df


def get_latest_adjustment_cost_report():
    adj_df = _get_adjustment_history()
    cost_df = _get_cost_history()
    filter_df = pd.read_csv(f"{PRODUCT_DIR}/{DocName.product_report}.{DocExt.csv}")
    # Merge adjustment history with price history
    report_df = adj_df.merge(cost_df, on = ["Invoice", "Product Number"], how = "left")
    # Drop duplicate products except the latest
    report_df.sort_values(by = ["Product Number", "Date"], inplace = True)
    report_df.drop_duplicates(["Product Number"], keep = "last", inplace = True)
    # Filter products
    report_df = filter_df.merge(report_df, how = "left", on = "Product Number")
    # Save Report
    write_to_csv(f"{PRODUCT_DIR}/{DocName.product_report}.{DocExt.csv}", report_df)
