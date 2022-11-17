import re

import multibajajmgt.client.odoo.client as odoo_client
import pandas as pd

from datetime import datetime, timedelta
from loguru import logger as log
from multibajajmgt.common import write_to_csv
from multibajajmgt.config import SALE_DIR


def _extract_product_id(row_df):
    """ Extract product ref from the data and set it in a column.

    :param row_df: pandas dataframe,
    :return: pandas dataframe,
    """
    row_df["db_id"] = row_df["product_id"][0]
    find = re.search(r"\[(.*?)]", row_df["product_id"][-1])
    row_df["internal_id"] = find.group(1)
    return row_df


def _fix_time_diff(from_date, to_date):
    """ Change from +0530(LK) time to 0000(Server) latitude time.

    Since Odoo server uses Time zone: Etc/UTC (UTC, +0000).
    From_date and to_date should be altered accordingly.

    :param from_date: str,
    :param to_date: str,
    :return: tuple,
    """
    time_diff = timedelta(hours = 5, minutes = 30)
    from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S") - time_diff
    from_date = f"{from_date}"
    if to_date:
        to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S") - time_diff
        to_date = f"{to_date}"
    return from_date, to_date


def export_sales_report(from_date, to_date = None):
    """ Export the sales report of list of product sale quantity between a date window.

    :param from_date: str,
    :param to_date: str,
    """
    log.info("Export sales report from: {} to: {}", from_date, to_date)
    # Fix time difference of the Odoo server
    from_date, to_date = _fix_time_diff(from_date, to_date)
    # Fetch report
    data = odoo_client.fetch_sale_report(from_date, to_date)
    report_df = pd.DataFrame(data)
    report_df = report_df.apply(_extract_product_id, axis = 1)
    report_df.drop(["__count", "__domain", "product_id"], axis = 1, inplace = True)
    write_to_csv(f"{SALE_DIR}/sale_product_report.csv", report_df,
                 header = ["DB ID", "Internal Reference", "Date", "Ordered Quantity"],
                 columns = ["db_id", "internal_id", "date:day", "product_uom_qty"])
