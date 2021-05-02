import csv
import json

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
        field_names = ("External ID","Product/External ID","Product/Internal Reference","Counted Quantity")
        csv_writer = csv.DictWriter(csvFile, fieldnames=field_names, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)

        csv_writer.writeheader()
        for product in odoo_products:
            csv_writer.writerow(product)


def inventory_adjustment(adjustment_file_path):
    adjusted_products = []
    with open(INVENTORY_ODOO_PATH, "r") as inventory_file, open(adjustment_file_path, "r") as adj_file:
        inventory_products = list(csv.DictReader(inventory_file))
        adj_products = list(csv.DictReader(adj_file))

    for idx, adj in enumerate(adj_products):
        adj_exists = False
        adj_part_number = adj["Part Number"]

        for inventory_product in inventory_products:
            if adj_part_number == inventory_product["Product/Internal Reference"]:
                inventory_quantity = float(inventory_product["Counted Quantity"])
                adjusted_quantity = float(adj["Quantity"])
                inventory_product["Counted Quantity"] = inventory_quantity + adjusted_quantity

                adjusted_products.append(inventory_product)
                adj_exists = True
                break

        if not adj_exists:
            print(f"Missing {adj_part_number}")

    with open(PRODUCTS_ODOO_PATH, mode='w') as csvFile:
        field_names = ("ID","Product/ID","Product/Internal Reference","Counted Quantity")
        csv_writer = csv.DictWriter(csvFile, fieldnames=field_names, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_MINIMAL)

        csv_writer.writeheader()
        for product in adjusted_products:
            csv_writer.writerow(product)


inventory_adjustment("../data/product/adjustments/adjustment-21-05-02.csv")
# update_quantity()
# enrich_final_products()
# format_full_products_file()
# find_missing_products(PRODUCTS_MULTI_PATH, PRODUCTS_PRICE_PATH)

# FILE_PATH = '../../data/product/catalogue/shop-catalogue.csv'
# FIELD_NAMES = ('Part Number', 'Quantity', 'Unit Price', 'Notes')


# def format_data():
#     finalised_products = []
#     unidentified_products = {'NOT FOUND': [], 'NO DATA': [], 'ZERO QUANTITY': []}
#     third_party_products = {
#         'YELLOW LABEL': [], 'SA': [], 'PAL': [], 'MILEX': [], 'MINDA': [], 'SD': [], 'BOSCH': [], 'MB': [], 'NACHi': [],
#         'JCM': [], 'NCL': [], 'Lumax': [], 'MacRo': [], 'Varroc': [], 'Flash': [], 'Champion': [], 'GLUE': [],
#         'ORIGINAL': [], 'LOCAL': [], 'UNKNOWN': []
#     }

#     catalogue = csv_to_json(FILE_PATH, FIELD_NAMES)

#     for idx, product in enumerate(catalogue):
#         note = product['Notes']
#         if note in ('NOT FOUND', 'NO DATA', 'ZERO QUANTITY'):
#             unidentified_products[note].append(product)
#         elif note in ('YELLOW LABEL', 'SA', 'PAL', 'MILEX', 'MINDA', 'SD', 'BOSCH', 'MB', 'NACHi', 'JCM', 'NCL',
#                       'Lumax', 'MacRo', 'Varroc', 'Flash', 'Champion', 'GLUE', 'ORIGINAL', 'LOCAL', 'UNKNOWN'):
#             product['Part Number'] = product['Part Number'].split("Y-")[-1]
#             third_party_products[note].append(product)
#         else:
#             finalised_products.append(product)

#     catalogue = {
#         'Finalised': finalised_products,
#         'Unidentified': unidentified_products,
#         'Third Party': third_party_products
#     }

#     data_file = open('../../data/product/catalogue/shop-catalogue(sorted).csv', 'w')
#     csv_writer = csv.writer(data_file)
#     csv_writer.writerow(FIELD_NAMES)
#     for catalogue_type in catalogue:
#         catalogues = catalogue[catalogue_type]
#         if catalogue_type == 'Finalised':
#             for product in catalogues:
#                 csv_writer.writerow([
#                     product['Part Number'], product['Quantity'], product['Unit Price'], product['Notes']
#                 ])
#         else:
#             for note in catalogues:
#                 products = catalogues[note]
#                 for product in products:
#                     csv_writer.writerow([
#                         product['Part Number'], product['Quantity'], product['Unit Price'], product['Notes']
#                     ])
#     data_file.close()


# def missing_products():
#     """
#     Detect duplicates in the final csv files
#     """
#     shop_reader = open('../../data/product/catalogue/shop-catalogue(sorted).csv', 'r')
#     odoo_reader = open('../../data/product/catalogue/odoo-catalogue.csv', 'r')

#     headers = ('Part Number', 'Quantity', 'Unit Price', 'Notes')
#     shop_catalogue = list(csv.DictReader(shop_reader, headers))
#     headers = ('Internal Reference', 'Display Name')
#     odoo_catalogue = list(csv.DictReader(odoo_reader, headers))

#     for shop_product in shop_catalogue:
#         is_found = False
#         part_number = shop_product['Part Number']
#         if shop_product['Notes'] == '':
#             for odoo_product in odoo_catalogue:
#                 if part_number == odoo_product['Internal Reference']:
#                     is_found = True
#             if not is_found:
#                 print(shop_product)


# def convert_to_csv():
#     with open(f'../../data/odoo-catalogue(priced).json') as f:
#         json_products = json.load(f)

#     with open(f'../../data/odoo-catalogue(priced).csv', mode='w') as csvFile:
#         csv_writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#         # csv_writer.writerow(get_template())

#         for json_product in json_products:
#             csv_writer.writerow(
#                 [f'{json_product["External ID"]}', f'{json_product["Internal Reference"]}', f'{json_product["Sales Price"]}',
#                  f'{json_product["Cost"]}'
#                  ])
#             print(json_product)


# update_prices()
# convert_to_csv()
# format_data()
# missing_products()
