import json
import csv

filePath = '/Users/yohanavishke/Documents/Projects/YohanAvishke/multi-bajaj-pos/data/'


def get_template():
    with open(f'{filePath}templates/products.csv') as csv_file:
        csv_template = csv.reader(csv_file, delimiter=',')
        for row in csv_template:
            return row


def enrich_products():
    enriched_products = []

    with open(f'{filePath}data files/product/products-category.json') as f:
        products_category = json.load(f)
    with open(f'{filePath}data files/product/products-pr.json') as f:
        products_pr = json.load(f)

    for product_category in products_category:
        for product_pr in products_pr:
            if product_category['Part Code'] == product_pr['Part Code']:
                description = product_category['Description'].replace('\n', '').replace('\r', '')
                # price = int(product_pr['Price'].replace(',', ''))

                enriched_product = {'Part Code': product_category['Part Code'],
                                    'Description': description,
                                    'Price': product_pr['Price'],
                                    'PR Code': product_pr['PR Code'],
                                    'Serial Base': product_category['Serial Base'],
                                    'Pro Hier Code': product_category['Pro Hier Code'],
                                    'MOQ Value': product_category['MOQ Value'],
                                    'Category': f'point_of_sale.{product_category["Part cat"]}'}
                enriched_products.append(enriched_product)
                print(enriched_product)
                break

    with open(f'{filePath}data files/product/products.json', 'w') as f:
        json.dump(enriched_products, f)


def generate_csv():
    with open(f'{filePath}data files/product/products.json') as f:
        json_products = json.load(f)

    with open(f'{filePath}data files/product/products.csv', mode='w') as csvFile:
        csv_writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(get_template())

        for json_product in json_products:
            csv_writer.writerow(
                [f'point_of_sale.{json_product["Part Code"]}', f'{json_product["Part Code"]}',
                 f'{json_product["Description"]}', f'{json_product["Part Code"]}',
                 f'{json_product["Description"]}', f'{json_product["Category"]}',
                 'Storable Product', f'{json_product["Price"]}', f'{json_product["Price"]}',
                 True, True, True
                 ])
            print(json_product)


enrich_products()
generate_csv()
