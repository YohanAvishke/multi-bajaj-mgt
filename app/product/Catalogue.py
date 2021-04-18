from app.Utils import *

FILE_PATH = '../../data/product/catalogue/shop-catalogue.csv'
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
            product['Part Number'] = product['Part Number'].split("Y-")[-1]
            third_party_products[note].append(product)
        else:
            finalised_products.append(product)

    catalogue = {
        'Finalised': finalised_products,
        'Unidentified': unidentified_products,
        'Third Party': third_party_products
    }

    data_file = open('../../data/product/catalogue/shop-catalogue(sorted).csv', 'w')
    csv_writer = csv.writer(data_file)
    csv_writer.writerow(FIELD_NAMES)
    for catalogue_type in catalogue:
        catalogues = catalogue[catalogue_type]
        if catalogue_type == 'Finalised':
            for product in catalogues:
                csv_writer.writerow([
                    product['Part Number'] , product['Quantity'], product['Unit Price'], product['Notes']
                ])
        else:
            for note in catalogues:
                products = catalogues[note]
                for product in products:
                    csv_writer.writerow([
                        product['Part Number'], product['Quantity'], product['Unit Price'], product['Notes']
                    ])
    data_file.close()




    # objects.append(OrderedDict([
    #     ("Part Number", "Part Number"), ("Quantity", "Quantity"), ("Unit Price", "Unit Price"), ("Notes", "Notes")
    # ]))
    # for key, value in enumerate(data_obj):
    #     print(f'{key} - {value}')
    # if row == 'Third Party':
    # for key, value in data_obj[row]:
    #     print(f'{key} - {value}')
    # if idx == 0:
    #     objects.append(OrderedDict([
    #         ("type", "Third Party"), ("Part Number", product["Part Number"]), ("Quantity", product["Quantity"]),
    #         ("Unit Price", product["Unit Price"]), ("Notes", product["Notes"])
    #     ]))
    # else:
    #     objects.append(OrderedDict([
    #         ("type", ""), ("Part Number", product["Part Number"]), ("Quantity", product["Quantity"]),
    #         ("Unit Price", product["Unit Price"]), ("Notes", product["Notes"])
    #     ]))
    #     elif row == 'Unidentified':
    #         print(type(data_obj[row]))
    #     else:
    #         print(type(data_obj[row]))
    # print(objects)

    # json_to_csv(data_obj=catalogue)


format_data()
