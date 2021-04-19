from app.Utils import *





















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


# def update_prices():
#     shop_reader = open('../../data/product/catalogue/shop-catalogue(sorted).csv', 'r')
#     odoo_reader = open('../../data/product.template.csv', 'r')
#     odoo_write = open('../../data/product/catalogue/odoo-catalogue(priced).csv', 'w')

#     headers = ('Part Number', 'Quantity', 'Unit Price', 'Notes')
#     shop_catalogue = list(csv.DictReader(shop_reader, headers))
#     headers = ('External ID', 'Internal Reference', 'Sales Price', 'Cost')
#     odoo_catalogue = list(csv.DictReader(odoo_reader, headers))

#     for idx, shop_product in enumerate(shop_catalogue):
#         part_number = shop_product['Part Number']
#         if shop_product['Notes'] == '':
#             for odoo_product in odoo_catalogue:
#                 if part_number == odoo_product['Internal Reference']:
#                     odoo_product['Sales Price'] = shop_product['Unit Price']
#                     odoo_product['Cost'] = shop_product['Unit Price']
#                     # print(idx)

#     # print(odoo_catalogue)
#     with open(f'../../data/odoo-catalogue(priced).json', 'w') as f:
#         json.dump(odoo_catalogue, f)

#     # with open(f'../../data/product/catalogue/odoo-catalogue(priced).csv', mode='w') as csvFile:
#     #     csv_writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#     #     for odoo_product in odoo_catalogue:
#     #         csv_writer.writerow(odoo_product)


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
convert_to_csv()
# format_data()
# missing_products()
