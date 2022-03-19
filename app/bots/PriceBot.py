import logging
import sys

import requests
import pandas as pd
import json
import app.clients.dpmc_client as dpmc_client

# -*- File Paths -*-
PRODUCT_PRICE_PATH = "../data/product/product.price.csv"
PRODUCT_UPDATED_PRICE_PATH = "../data/product/product.price.updated.csv"
PRODUCT_EMPTY_STOCK_PRICE_PATH = "../data/product/product.price-empty-stock.csv"

# -*- Request URLs -*-
URL = "https://erp.dpg.lk/PADEALER/PADLRItemInquiry/Inquire"

# -*- Constants -*-
HEADERS = {
    "authority": "erp.dpg.lk",
    "sec-ch-ua": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "accept": "*/*",
    "x-requested-with": "XMLHttpRequest",
    "sec-ch-ua-mobile": "?0",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/90.0.4430.72 Mobile Safari/537.36",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://erp.dpg.lk",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://erp.dpg.lk/Application/Home/PADEALER",
    "accept-language": "en-US,en;q=0.9"
    }


# -*- Function -*-
def fetch_prices():
    df = pd.read_csv(PRODUCT_PRICE_PATH)
    if "Updated Sales Price" not in df.columns:
        df["Updated Sales Price"] = df["Updated Cost"] = df["Status"] = None
        df.to_csv(PRODUCT_PRICE_PATH, index = False)

    for idx, row in df.iterrows():
        if "Bajaj" in row["Point of Sale Category"] and pd.isnull(row["Updated Cost"]):
            product_number = row["Internal Reference"]
            payload = f"strPartNo_PAItemInq={product_number}&" \
                      "strFuncType=INVENTORYDATA&" \
                      "strPADealerCode_PAItemInq=AC2011063676&" \
                      "STR_FORM_ID=00602&" \
                      "STR_FUNCTION_ID=IQ&" \
                      "STR_PREMIS=KGL&" \
                      "STR_INSTANT=DLR&" \
                      "STR_APP_ID=00011"
            try:
                response = requests.request("POST", URL, headers = HEADERS, data = payload)
            except requests.exceptions.ConnectionError as e:
                logging.error(e)
                sys.exit(0)

            if response:
                product_data = json.loads(response.text)["DATA"]
                if "dblSellingPrice" in product_data and product_data["dblSellingPrice"]:
                    price = float(product_data["dblSellingPrice"])
                    df.loc[idx, "Updated Sales Price"] = df.loc[idx, "Updated Cost"] = price

                    if float(row["Sales Price"]) > price:
                        df.loc[idx, "Status"] = "down"
                    elif float(row["Sales Price"]) < price:
                        df.loc[idx, "Status"] = "up"
                    else:
                        df.loc[idx, "Status"] = "equal"

                    logging.info(f"{idx + 1} - Product Number: {product_number}, Price: {price}")
                else:
                    df.loc[idx, "Updated Sales Price"] = df.loc[idx, "Sales Price"]
                    df.loc[idx, "Updated Cost"] = df.loc[idx, "Cost"]
                    df.loc[idx, "Status"] = "none"

                    logging.warning(f"{idx + 1} - Product Number: {product_number} is Invalid !!!")

                df.to_csv(PRODUCT_PRICE_PATH, index = False)
                filter_by_status(df, ['up', 'down'])
            else:
                logging.error(f"An error has occurred with the request !!! \n"
                              f"Status: {response.status_code} ,For reason: {response.reason}")
                main()
                sys.exit(0)
            # time.sleep(5)
        else:
            df.loc[idx, "Updated Sales Price"] = df.loc[idx, "Sales Price"]
            df.loc[idx, "Updated Cost"] = df.loc[idx, "Cost"]
            df.loc[idx, "Status"] = "none"
    return df


def filter_by_status(df, options):
    df = df[df['Status'].isin(options)]
    df.to_csv(PRODUCT_UPDATED_PRICE_PATH, index = False)
    return df


def sort_products_by_price():
    df = pd.read_csv(PRODUCT_EMPTY_STOCK_PRICE_PATH, header = 0)
    sorted_df = df.sort_values(by = "Sales Price", ascending = False)
    sorted_df.to_csv(PRODUCT_EMPTY_STOCK_PRICE_PATH, index = False)


def get_price_fluctuations():
    price_reader = pd.read_csv(PRODUCT_PRICE_PATH, header = 0)
    a = price_reader[["Sales Price"]].eq(price_reader["Updated Sales Price"], axis = 0).assign(no = True)


def main():
    HEADERS["cookie"] = dpmc_client.authenticate()
    logging.info(f"Session created")
    products_df = fetch_prices()
    filter_by_status(products_df, ['up', 'down'])


if __name__ == "__main__":
    # logging config
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")
    # pandas config
    pd.set_option("display.expand_frame_repr", False)
    pd.set_option("display.max_rows", 25)
    main()
