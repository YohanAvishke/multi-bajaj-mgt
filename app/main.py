from app.config import ROOT_DIR

import requests
import app.clients.dpmc_client as dpmc_client
import pandas as pd

headers = {
    'authority': 'erp.dpg.lk',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
    'accept': '*/*',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/97.0.4692.99 Safari/537.36',
    'sec-ch-ua-platform': '"macOS"',
    'origin': 'https://erp.dpg.lk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
    'accept-language': 'en-US,en;q=0.9',
    'dnt': '1',
    'sec-gpc': '1',
    }

FILE = f'{ROOT_DIR}/data/product/product.template.csv'


def main(product_df):
    product_number = product_df["Internal Reference"]
    data = {
        'strDealerCode_PADLROrder': 'AC2011063676',
        'strPADealerShipCat_PADLROrder': 'KDLR',
        'strPartCode_PADLROrder': f'{product_number}',
        'strInstanceId_PADLROrder': 'BAJ',
        'strInqType_PADLROrder': 'PARTPRICE',
        'STR_FORM_ID': '00596',
        'STR_FUNCTION_ID': 'CR',
        'STR_PREMIS': 'KGL',
        'STR_INSTANT': 'DLR',
        'STR_APP_ID': '00011'
        }
    response = requests.post('https://erp.dpg.lk/PADealer/PADLROrder/Inquire', headers = headers, data = data)
    if response.ok and response.text != "":
        response = response.json()
        product_df["Discount"] = response["DATA"]["dblDiscount_PADLROrder"]
    else:
        product_df["Discount"] = "NoData"
    print(f"{product_number} - {product_df['Discount']}")
    return product_df


if __name__ == "__main__":
    headers["cookie"] = dpmc_client.authenticate()
    products_df = pd.read_csv(FILE)
    products_df = products_df.apply(main, axis = 1)
    products_df.to_csv(FILE, index = False)
