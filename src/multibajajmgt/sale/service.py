import re

import multibajajmgt.client.odoo.client as odoo_client
import pandas as pd

from multibajajmgt.common import write_to_csv
from multibajajmgt.config import SALE_DIR


def _extract_product_id(df):
    df["db_id"] = df["product_id"][0]
    find = re.search(r"\[(.*?)]", df["product_id"][-1])
    df["internal_id"] = find.group(1)
    return df


# SL time is 5 and 1/2 hours ahead of odoo server
def export_sales_report(from_date, to_date = None):
    data = odoo_client.fetch_sale_report(from_date, to_date)
    df = pd.DataFrame(data)
    df = df.apply(_extract_product_id, axis = 1)
    df.drop(["__count", "__domain", "product_id"], axis = 1, inplace = True)
    write_to_csv(f"{SALE_DIR}/sale_product_report.csv", df,
                 header = ["DB ID", "Internal Reference", "Date", "Ordered Quantity"],
                 columns = ["db_id", "internal_id", "date:day", "product_uom_qty"])
