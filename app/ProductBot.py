import csv
import json
import requests

CATEGORIES_ERP_PATH = "../../data/category/categories(erp).json"
PRODUCTS_FULL_PATH = "../../data/product/products(full).json"
PRODUCTS_FINAL_PATH = "../../data/product/products(final).json"
PRODUCTS_MULTI_PATH = "../data/product/products(multi).csv"
PRODUCTS_ODOO_PATH = "../data/product/products(odoo).csv"
PRODUCTS_PRICE_PATH = "../data/product/products(price).csv"
INVENTORY_ODOO_PATH = "../data/product/adjustments/stock.inventory.line.csv"


def format_full_products_file():
    with open(PRODUCTS_FULL_PATH) as file:
        products = json.load(file)

        for idx, product in enumerate(products):
            product.pop('Status', None)
            formatted_description = product['Product Description'].replace('\n', '').replace('\r', '').replace('\t', '')
            product['Product Description'] = f"{product['Part Code']} | [{formatted_description}]"
            print(idx)

    with open(PRODUCTS_FINAL_PATH, "w") as file:
        json.dump(products, file)


def enrich_final_products():
    with open(CATEGORIES_ERP_PATH) as erp_categories_file:
        categories = json.load(erp_categories_file)
    with open(PRODUCTS_MULTI_PATH, 'r') as prices_file:
        prices = list(csv.DictReader(prices_file))
    with open(PRODUCTS_FINAL_PATH) as products_file:
        products = json.load(products_file)

    for product in products:
        product_category_id = product["Part Category"]
        product_code = product["Part Code"]
        price_exists = False

        for category in categories:
            if product_category_id == category["Category Code"]:
                product["Part Category"] = category["Description"]
                break

        for priced_product in prices:
            if product_code == priced_product["Part Number"]:
                price = priced_product["Price"]
                if price != "":
                    product["Price"] = int(price)
                price_exists = True
                break
        if not price_exists:
            product["Price"] = 0
            print(product_code)

    with open(PRODUCTS_FINAL_PATH, "w") as file:
        json.dump(products, file)


def find_missing_products(source_path, comparer_path):
    with open(source_path, "r") as source_file, open(comparer_path, "r") as comparer_file:
        source_reader = list(csv.DictReader(source_file))
        comparer_reader = list(csv.DictReader(comparer_file))

        for source in source_reader:
            source_part_number = source['Part Number']
            source_note = source["Notes"]

            if source_note == "":
                is_missing = True

                for comparer in comparer_reader:
                    if source_part_number == comparer['PART_NO']:
                        is_missing = False
                if is_missing:
                    print(f"Missing {source_part_number}")


def update_quantity():
    with open(INVENTORY_ODOO_PATH, "r") as odoo_file, open(PRODUCTS_MULTI_PATH, "r") as multi_file:
        odoo_products = list(csv.DictReader(odoo_file))
        multi_products = list(csv.DictReader(multi_file))

    for idx, multi_product in enumerate(multi_products):
        multi_part_number = multi_product["Part Number"]

        if multi_product["Notes"] == "":
            for odoo_product in odoo_products:
                if multi_part_number == odoo_product["Product/Internal Reference"]:
                    odoo_product["Counted Quantity"] += multi_product["Quantity"]
                    print(idx)
                    break

    with open(PRODUCTS_ODOO_PATH, mode='w') as csvFile:
        field_names = ("External ID", "Product/External ID", "Product/Internal Reference", "Counted Quantity")
        csv_writer = csv.DictWriter(csvFile, fieldnames=field_names, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)

        csv_writer.writeheader()
        for product in odoo_products:
            csv_writer.writerow(product)


def scrap_categories():
    url = "https://erp.dpg.lk/Help/EnterPress"

    headers = {
        'authority': 'erp.dpg.lk',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/90.0.4430.93 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://erp.dpg.lk',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': '.AspNetCore.Session=CfDJ8N8gIs%2FXx8JIrXltjeQ28vFI9s%2F8wmJ643e2fNePr7we7AemM0wbkub3WyXT2IYsn3sIO'
                  'P%2F02eKCF8toZlaCtGxu%2FV9Yop4w9B90m%2BpCaUBQ2vt4zBZwljqEqMx7Otspc8QL%2FixZTN5Y1v4hkztinn0PCzQ8bwr'
                  '3wLI8tMPW4g8h; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8N8gIs_Xx8JIrXltjeQ28vHKrxQ5gC2_4GrCt0RQDQm'
                  'TVay0r_yc8Vsp1Pqx4kmdA1Cv6mpPE3SsC6NZZ96XZvoj4iRafCp2Nz_RJDrDUYG5oUKZckaDPTuVIJI0d2otNskc_muerV7Rb'
                  '7O5Hy7aRb8'
    }

    products = []

    for number in products:
        payload = "strInstance=DLR&strPremises=KGL&strAppID=00011&strFORMID=00596&strHELP_TITEL=Part+Details&" \
                  "arrFIELD_NAME%5B%5D=STR_PART_NO&arrFIELD_NAME%5B%5D=STR_DESC&arrFIELD_NAME%5B%5D=STR_CAT_CODE&" \
                  "arrFIELD_NAME%5B%5D=STR_SERIAL_STATUS&arrFIELD_NAME%5B%5D=STR_PROD_HIER_CODE&" \
                  "arrFIELD_NAME%5B%5D=INT_MOQ&arrHIDEN_FIELD_INDEX%5B%5D=2&arrHIDEN_FIELD_INDEX%5B%5D=3" \
                  "&arrHIDEN_FIELD_INDEX%5B%5D=4&arrHIDEN_FIELD_INDEX%5B%5D=5&arrDISPLAY_NAME%5B%5D=Part+Code&" \
                  "arrDISPLAY_NAME%5B%5D=Description&arrDISPLAY_NAME%5B%5D=Part+cat&" \
                  "arrDISPLAY_NAME%5B%5D=Serial+Base&arrDISPLAY_NAME%5B%5D=Pro+Hier+Code&" \
                  "arrDISPLAY_NAME%5B%5D=MOQ+Value&strORDERBY%5B%5D=STR_PART_NO&arrSEARCH_TEXT%5B%5D=STR_PART_NO&" \
                  f"arrSEARCH_TEXT%5B%5D={number}&strOTHER_WHERE_CONDITION%5B0%5D%5B%5D=STR_PROD_HIER_CODE&" \
                  "strOTHER_WHERE_CONDITION%5B0%5D%5B%5D=IN&" \
                  "strOTHER_WHERE_CONDITION%5B0%5D%5B%5D=('BAJ'%2C'KTM')&strLIMIT=50&strARCHIVE=TRUE&" \
                  "strAPI_URL=api%2FModules%2FPADealer%2FPADLROrder%2FPartList&" \
                  "strCallbackFunction=fncbPADealerOrder_CallBack()&strSchema="

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            data = json.loads(response.text)[0]
            if 'Part cat' in data:
                print(f"{number} : {data['Part cat']}")
            else:
                print(f'{number} - Not Found.')
        else:
            print(f'{number} - Not Found.')
