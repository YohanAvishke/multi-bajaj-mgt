from app.Utils import *

FILE_PATH = '../../data/product/catalogue.csv'
FIELD_NAMES = ('Part Number', 'Quantity', 'Unit Price', 'Notes')


def format_data():
    finalised_products = []
    unidentified_products = {'NOT FOUND': [], 'NO DATA': [], 'ZERO QUANTITY': []}
    third_party_products = {
        'YELLOW LABEL': [], 'SA': [], 'PAL': [], 'MILEX': [], 'MINDA': [], 'SD': [], 'BOSCH': [], 'MB': [], 'NACHi': [],
        'JCM': [], 'NCL': [], 'GLUE': [], 'ORIGINAL': [], 'LOCAL': [], 'UNKNOWN': []
    }

    catalogue = csv_to_json(FILE_PATH, FIELD_NAMES)

    for idx, product in enumerate(catalogue):
        note = product['Notes']
        if note in ('NOT FOUND', 'NO DATA', 'ZERO QUANTITY'):
            unidentified_products[note].append(product)
        elif note in ('YELLOW LABEL', 'SA', 'PAL', 'MILEX', 'MINDA', 'SD', 'BOSCH', 'MB', 'NACHi', 'JCM', 'NCL', 'GLUE',
                      'ORIGINAL', 'LOCAL', 'UNKNOWN'):
            third_party_products[note].append(product)
        else:
            finalised_products.append(product)

    catalogue = {
        'Finalised': finalised_products,
        'Unidentified': unidentified_products,
        'Third Party': third_party_products
    }
    print(catalogue)


format_data()
