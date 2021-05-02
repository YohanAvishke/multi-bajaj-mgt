import logging
import threading
import requests
import csv
import json
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
	    'cookie': '.AspNetCore.Session=CfDJ8N8gIs%2FXx8JIrXltjeQ28vFI9s%2F8wmJ643e2fNePr7we7AemM0wbkub3WyXT2IYsn3sIOP%2F02eKCF8toZlaCtGxu%2FV9Yop4w9B90m%2BpCaUBQ2vt4zBZwljqEqMx7Otspc8QL%2FixZTN5Y1v4hkztinn0PCzQ8bwr3wLI8tMPW4g8h; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8N8gIs_Xx8JIrXltjeQ28vHKrxQ5gC2_4GrCt0RQDQmTVay0r_yc8Vsp1Pqx4kmdA1Cv6mpPE3SsC6NZZ96XZvoj4iRafCp2Nz_RJDrDUYG5oUKZckaDPTuVIJI0d2otNskc_muerV7Rb7O5Hy7aRb8'
	}

	with open(PRODUCT_PATH, "r") as product_file:
		products = list(csv.DictReader(product_file))

	# chunks = split_list(products, CHUNK_SIZE)
	# for idx, chunk in enumerate(chunks):
	# 	if idx == READ_STATE:
	# 		updatable_list = chunk
	logging.info(f"Starting params - State: {READ_STATE}, chunk_size: {CHUNK_SIZE}, chunks: {len(products)//CHUNK_SIZE}, left-over: {len(products)%3}")

	for product in products:
		# print(product['Internal ref'])
		number = product['Internal ref']
		payload = f"strPartNo_PAItemInq={number}&strFuncType=INVENTORYDATA&strPADealerCode_PAItemInq=AC2011063676&STR_" \
				"FORM_ID=00602&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&STR_INSTANT=DLR&STR_APP_ID=00011"
		response = requests.request("POST", URL, headers=HEADERS, data=payload)

		if response.status_code == 200:
			data = json.loads(response.text)["DATA"]

			if 'dblSellingPrice' in data:
				print(f"{product['Internal ref']} : {data['dblSellingPrice']}")
			else:
				print(f'{number} - Not Found.')
		else:
			print(f'{number} - Not Found.')
		time.sleep(5)


def split_list(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))


scrap_prices()