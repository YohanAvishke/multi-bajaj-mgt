import logging
import threading
import requests
import csv
import time

PRODUCT_PATH = "../data/product/price-update-list.csv"
READ_STATE = 0
CHUNK_SIZE = 869

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

def scrap_prices():
	URL = "https://erp.dpg.lk/PADEALER/PADLRItemInquiry/Inquire"
	HEADERS = {
	    'authority': 'erp.dpg.lk',
	    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
	    'accept': '*/*',
	    'x-requested-with': 'XMLHttpRequest',
	    'sec-ch-ua-mobile': '?0',
	    'user-agent': 'Mozilla/5.0 (Linux; Android 10; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Mobile Safari/537.36',
	    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
	    'origin': 'https://erp.dpg.lk',
	    'sec-fetch-site': 'same-origin',
	    'sec-fetch-mode': 'cors',
	    'sec-fetch-dest': 'empty',
	    'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
	    'accept-language': 'en-US,en;q=0.9',
	    'cookie': '.AspNetCore.Session=CfDJ8N8gIs%2FXx8JIrXltjeQ28vHjNs2C2TTMszoi12z%2FTbuUts5QZfhQrtCOXHuOPBCHMPelg5Di5Mmkiq0shyn7XtDVTYeQIDwOjRhOHcguzyMr7NWR0je3lmZ%2B2wq4cNtzcA3AILi58Cg%2B7dEa8kzCKZZXRIJXv3oMovXVyzq87EwE; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8N8gIs_Xx8JIrXltjeQ28vFrliv6_JH_DRd-QA4_mqcCKxaopTA-aF3lVkTXH3nyczAvdvMJaug0hRJxw_RNFmnW1nl9SE1IF_dmghugj3OTnj_3Q8mHEH5YQcZMyaKSsUkv2eplYGhkPGnXNgeqZck'
	}

	with open(PRODUCT_PATH, "r") as product_file:
		products = list(csv.DictReader(product_file))

	chunks = split_list(products, CHUNK_SIZE)
	for idx, chunk in enumerate(chunks):
		if idx == READ_STATE:
			updatable_list = chunk
	logging.info(f"Starting params - State: {READ_STATE}, chunk_size: {CHUNK_SIZE}, chunks: {len(products)//CHUNK_SIZE}, left-over: {len(products)%3}")

	for product in updatable_list:
		payload = f"strPartNo_PAItemInq={product['Internal ref']}&strFuncType=INVENTORYDATA&strPADealerCode_PAItemInq=AC2011063676&STR_" \
				"FORM_ID=00602&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&STR_INSTANT=DLR&STR_APP_ID=00011"
		# response = requests.request("POST", URL, headers=HEADERS, data=payload)

		# if response.status_code == 200:
  #       	data = json.loads(response.text)["DATA"]
	 #        if 'dblSellingPrice' in data:
	 #            print(data["dblSellingPrice"])
	 #        else:
	 #            print(f'{number} - Not Found.')
	 #    else:
	 #        print(f'{number} - Not Found.')


def split_list(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))


scrap_prices()