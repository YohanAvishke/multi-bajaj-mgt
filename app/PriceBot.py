import logging
import requests
import csv
import json
import time

# -*- File Paths -*-
PRODUCT_PATH = "../data/product/product.price.csv"

# -*- Request URLs -*-
URL = "https://erp.dpg.lk/PADEALER/PADLRItemInquiry/Inquire"

# -*- Request Headers -*-
HEADERS = {
    'authority': 'erp.dpg.lk',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'accept': '*/*',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/90.0.4430.72 Mobile Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://erp.dpg.lk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': '.AspNetCore.Session=CfDJ8N8gIs%2FXx8JIrXltjeQ28vGUovewhiCGa7dBuOOJEHlraIPQTMUBK7cCBgs%2ByZUcbHVSJ6'
              'kozamdoMdGQogLFEX7NUdaFd8TKnQdHMkE7LjNuEwMTCHizHN2yzUB5wz8N9raKnEPvYPx5xRsjlWM%2BySf2yupM3k7kxtv7sN'
              'Ob0cz; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8N8gIs_Xx8JIrXltjeQ28vHnbaej-dcUfNA-e_pAj5cHEKQI3eKb'
              'nurde3xlktWSsMzzMjv3MYTvLXIV2HxB7g0xmG_P7wDzQ0iRsQnkJw43kvDjwv-qGjKzDvKq_cmnD8x_n_P-g43sm9BR2n_dKaw'
}

# -*- Main function -*-
if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s- %(message)s"
    logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")


# -*- Function -*-
def scrap_prices():
    with open(PRODUCT_PATH, "r") as product_file:
        product_reader = list(csv.DictReader(product_file))

    for product in product_reader:
        number = product['Internal Reference']
        category = product['Point of Sale Category']

        if "Bajaj" in category:
            payload = f"strPartNo_PAItemInq={number}&strFuncType=INVENTORYDATA&" \
                      "strPADealerCode_PAItemInq=AC2011063676&STR_FORM_ID=00602&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&" \
                      "STR_INSTANT=DLR&STR_APP_ID=00011"
            response = requests.request("POST", URL, headers=HEADERS, data=payload)

            if response:
                product_data = json.loads(response.text)["DATA"]
                if 'dblSellingPrice' in product_data:
                    logging.info(f"{product['Internal ref']} : {product_data['dblSellingPrice']}")
                else:
                    logging.warning(f"Product Number: {number} is Invalid !!!")
            else:
                logging.error(f'An error has occurred !!! \nStatus: {response.status_code} \n'
                              f'For reason: {response.reason}')

            time.sleep(5)


# -*- Function Calls -*-
scrap_prices()
