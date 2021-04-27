import requests

PRODUCT_PATH = "../data/products/price-update-list.csv"

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
	    'cookie': '.AspNetCore.Session=CfDJ8H8TYQJVgJRGttyTw7gWFEZoDWDrYJsPTYLKqZdcoYdyYhG3ggsoMRkYnL7V1g5pLuXUNpLdOeaUW%2BLAIHd0Mrvle4KtcFHJ0nGqyZZnOCzkUmX6obnOebX30RNKAj%2FkJH%2BMQ8%2FRZKmkxhoPrFIG9pB%2FcpmD5jNd8qRZMe4IsxYh; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8H8TYQJVgJRGttyTw7gWFEawVVW-1-ZcXNH31kg-kamO9B4yfGVKSI5EoxMByzV1CoJk8oA0Qp0mCkNsTqWsvRJtpTyagST5kjTPd5icsGtdPabpCxdvOnAGunsuP6OON-nDcPMTAuqmmNg8NfNS0k0'
	}

	with open(PRODUCT_PATH, "r") as product_file:
		products = list(csv.DictReader(product_file))