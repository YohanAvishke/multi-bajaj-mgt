import logging
import requests
import pandas
import json
import time

# -*- File Paths -*-
PRODUCT_PRICE_PATH = "../data/product/product.price.csv"

# -*- Request URLs -*-
URL = "https://erp.dpg.lk/PADEALER/PADLRItemInquiry/Inquire"

# -*- Request Headers -*-
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
    "accept-language": "en-US,en;q=0.9",
    "cookie": ".AspNetCore.Session=CfDJ8GocJQ9OP09IpVQeLLXSxcbUDQHZT%2F%2Ffy49MbynwtHp%2BNdShxwbOHGlUbvlFHyzt1Te%2Fsew"
              "4n%2B3caRe2xuPk5gro7L7QPRQY%2F79esBeLug%2BABm3XEYPsyIRJ9pgo7VoDkxbayoj7VKFMYRbytOHvaUtTmzPMLI2p%2BIc4vH"
              "ti8IL0; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8GocJQ9OP09IpVQeLLXSxcaqF1vwV7O1_aXIilySduqGkLf1AvALruR"
              "rIJJUE9EsRVER7xkYfENOJg1mihpkC5P97XflLltnJu6ajao_fS-jAw--Os870u6OR1otQsYevzDS4rRhu0uK45ENX32ROOw"
    }

# -*- Main function -*-
if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")


# -*- Function -*-
def scrap_prices():
    product_reader = pandas.read_csv(PRODUCT_PRICE_PATH)

    for idx, product in product_reader.iterrows():
        if "Bajaj" in product["Point of Sale Category"] and pandas.isnull(product["Updated Cost"]):
            product_number = product['Internal Reference']

            payload = f"strPartNo_PAItemInq={product_number}&strFuncType=INVENTORYDATA&" \
                      "strPADealerCode_PAItemInq=AC2011063676&STR_FORM_ID=00602&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&" \
                      "STR_INSTANT=DLR&STR_APP_ID=00011"

            try:
                response = requests.request("POST", URL, headers = HEADERS, data = payload)
            except requests.exceptions.ConnectionError as e:
                logging.error(e)
                break

            if response:
                product_data = json.loads(response.text)["DATA"]

                if 'dblSellingPrice' in product_data and product_data["dblSellingPrice"]:
                    price = float(product_data["dblSellingPrice"])

                    product_reader.loc[idx, "Updated Sales Price"] = product_reader.loc[idx, "Updated Cost"] = price
                    logging.info(f"{idx + 1} - Product Number: {product_number}, Price: {price}")
                else:
                    product_reader.loc[idx, "Updated Sales Price"] = product_reader.loc[idx, "Updated Cost"] = "-"
                    logging.warning(f"Product Number: {product_number} is Invalid !!!")

                product_reader.to_csv(PRODUCT_PRICE_PATH, index = False)

            else:
                logging.error(f'An error has occurred !!! \nStatus: {response.status_code} \n'
                              f'For reason: {response.reason}')
                break
            time.sleep(5)


def get_price_fluctuations():
    price_reader = pandas.read_csv(PRODUCT_PRICE_PATH, header = 0)
    a = price_reader[["Sales Price"]].eq(price_reader["Updated Sales Price"], axis = 0).assign(no = True)


# -*- Function Calls -*-
scrap_prices()
