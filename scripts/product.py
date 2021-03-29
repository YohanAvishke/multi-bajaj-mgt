import json
import csv

filePath = '/Users/yohanavishke/Documents/Projects/YohanAvishke/multi-bajaj-pos/data/'


def convert_to_json():
    """
    Convert product_prices to json from csv
    """
    csv_file = open(f'{filePath}data files/product/product-prices.csv', 'r')
    json_file = open(f'{filePath}data files/product/product-prices.json', 'w')

    column_names = ('PART_NO', 'PART_DESC', 'PR CODE', 'SELLING PRICE')
    reader = csv.DictReader(csv_file, column_names)

    json_file.write('[')
    for idx, row in enumerate(reader):
        if idx != 0:
            json.dump(row, json_file)
            json_file.write(',\n')
    json_file.write(']')


def reformat_data():
    """
    Update product_prices from product_categories' description and price as those can contain non-formatted strings
    """
    with open(f'{filePath}data files/product/product-categories.json') as f:
        product_categories = json.load(f)
    with open(f'{filePath}data files/product/product-prices.json') as f:
        product_prices = json.load(f)

    for product_price in product_prices:
        product_price['SELLING PRICE'] = float(product_price['SELLING PRICE'].replace(',', ''))

        for product_category in product_categories:
            if product_price['PART_NO'] == product_category['Part Code']:
                desc = product_category['Product Description'].replace('\n', '').replace('\r', '').replace('\t', '')
                product_price['PART_DESC'] = desc
                print(product_price)
                break

    json_file = open(f'{filePath}data files/product/product-prices.json', 'w')
    json.dump(product_prices, json_file)


def add_categories():
    """
    Add categories to the products and write them to a different json file
    """
    with open(f'{filePath}data files/product/product-details.json') as f:
        product_details = json.load(f)
    with open(f'{filePath}data files/product/product-prices.json') as f:
        product_prices = json.load(f)

    for product_price in product_prices:
        for product_detail in product_details:
            if product_price['PART_NO'] == product_detail['Part Code']:
                product_price['CATEGORY'] = f'point_of_sale.{product_detail["Part cat"]}'
                print(product_price)
                break

    with open(f'{filePath}data files/product/products.json', 'w') as f:
        json.dump(product_prices, f)


def convert_to_csv():
    with open(f'{filePath}data files/product/products.json') as f:
        json_products = json.load(f)

    with open(f'{filePath}data files/product/products.csv', mode='w') as csvFile:
        csv_writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(get_template())

        for json_product in json_products:
            csv_writer.writerow(
                [f'point_of_sale.{json_product["PART_NO"]}', f'{json_product["PART_NO"]}',
                 f'{json_product["PART_DESC"]}', f'{json_product["PART_NO"]}',
                 f'{json_product["PART_DESC"]}', f'{json_product["CATEGORY"]}',
                 'Storable Product', f'{json_product["SELLING PRICE"]}', f'{json_product["SELLING PRICE"]}',
                 True, True, True
                 ])
            print(json_product)


def get_template():
    with open(f'{filePath}templates/products.csv') as csv_file:
        csv_template = csv.reader(csv_file, delimiter=',')
        for row in csv_template:
            return row


def validate_data():
    """
    Detect duplicates in the final csv file
    """
    products = open(f'{filePath}data files/product/products.csv', 'r')
    existing_products = open(f'{filePath}data files/product/product.template.csv', 'r')
    column_names = ('External ID', 'Internal Reference', 'Name', 'Barcode', 'Description',
                    'Product Category/External ID', 'Product Type', 'Sales Price', 'Available in POS',
                    'Can be Purchased', 'Can be Sold')
    products_r = list(csv.DictReader(products, column_names))
    column_names = ('Internal Reference', 'Display Name')
    existing_products_r = list(csv.DictReader(existing_products, column_names))

    count = 0
    for product_r1 in products_r:
        flag = False
        for product_r2 in products_r:
            if product_r1['Internal Reference'] == product_r2['Internal Reference']:
                if flag:
                    print(f'Duplicate {product_r1["Internal Reference"]}')
                flag = True
                count += 1
        # if flag:
        #     print(count)
    # for product_r in products_r:
    #     flag = False
    #     for existing_product_r in existing_products_r:
    #         if product_r['Internal Reference'] == existing_product_r['Internal Reference']:
    #             flag = True
    #             break
    #     if not flag:
    #         print(product_r['Internal Reference'])

# convert_to_json()
# TODO: remove last comma from last object for next cmd to work in product_prices.json(Only if convert_to_json() has
#  been called before)
# reformat_data()
# add_categories()
# convert_to_csv()
# validate_data()
