import json
import csv

filePath = '/Users/yohanavishke/Documents/Projects/YohanAvishke/multi-bajaj-pos/data/'


def get_template():
    with open(f'{filePath}templates/products.csv') as csv_file:
        csv_template = csv.reader(csv_file, delimiter=',')
        for row in csv_template:
            return row


def convert_to_json():
    csv_file = open(f'{filePath}data files/product/product-prices.csv', 'r')
    json_file = open(f'{filePath}data files/product/product-prices.json', 'w')

    column_names = ('PART_NO', 'PART_DESC', 'PR CODE', 'SELLING PRICE')
    reader = csv.DictReader(csv_file, column_names)

    json_file.write('[')
    for idx, row in enumerate(reader):
        if idx != 0:
            desc = row['PART_DESC']
            price = row['SELLING PRICE']

            newline_pieces = desc.split('\n')
            newline_pieces_size = len(newline_pieces)
            if newline_pieces_size == 2:
                if newline_pieces[0] != '':
                    desc = newline_pieces[0]
                elif newline_pieces[1] != '':
                    desc = newline_pieces[1]
                else:
                    print(f'{row["PART_NO"]} - ALERT: PIECE SIZE: 2, BOTH ARE EMPTY')
                    exit(2)
            elif newline_pieces_size == 3:
                if newline_pieces[0] != '':
                    desc = newline_pieces[0]
                elif newline_pieces[1] != '':
                    desc = newline_pieces[1]
                elif newline_pieces[2] != '':
                    desc = newline_pieces[2]
                else:
                    print(f'{row["PART_NO"]} - ALERT: PIECE SIZE: 3, ALL ARE EMPTY')
                    exit(2)
            elif newline_pieces_size == 4:
                if newline_pieces[0] != '':
                    desc = newline_pieces[0]
                elif newline_pieces[1] != '':
                    desc = newline_pieces[1]
                elif newline_pieces[2] != '':
                    desc = newline_pieces[2]
                elif newline_pieces[3] != '':
                    desc = newline_pieces[3]
                else:
                    print(f'{row["PART_NO"]} - ALERT: PIECE SIZE: 4, ALL ARE EMPTY')
                    exit(2)
            elif newline_pieces_size > 4:
                print(f'{row["PART_NO"]} - ALERT: PIECE SIZE: {newline_pieces_size}')
                exit(2)

            desc = desc.replace('\n', '').replace('\r', '')
            row['PART_DESC'] = desc.replace('\u00a0', ' ').replace('\u201c', '').replace('\u201d', '') \
                .replace('\u00bf', '-').replace('\u00d8', '0')

            price = int(price.replace(',', ''))
            row['SELLING PRICE'] = price

            json.dump(row, json_file)
            json_file.write(',\n')
    json_file.write(']')


def test():
    with open(f'{filePath}data files/product/product-categories') as f:
        product_categories = json.load(f)
    with open(f'{filePath}data files/product/product-prices.json') as f:
        product_prices = json.load(f)


def enrich_products():
    enriched_products = []

    with open(f'{filePath}data files/product/product-categories') as f:
        product_categories = json.load(f)
    with open(f'{filePath}data files/product/product-prices.csv') as f:
        product_prices = csv.DictReader(f)

    # for product_price in product_prices:
    #     for product_category in product_categories:
    #         if product_category['Part Code'] == product_pr['Part Code'] and product_category['Pro Hier Code'] == 'BAJ':
    #             description = product_category['Description'].replace('\n', '').replace('\r', '')
    #             # price = int(product_pr['Price'].replace(',', ''))
    #
    #             enriched_product = {'Part Code': product_category['Part Code'],
    #                                 'Description': description,
    #                                 'Price': product_pr['Price'],
    #                                 'PR Code': product_pr['PR Code'],
    #                                 'Serial Base': product_category['Serial Base'],
    #                                 'Pro Hier Code': product_category['Pro Hier Code'],
    #                                 'MOQ Value': product_category['MOQ Value'],
    #                                 'Category': f'point_of_sale.{product_category["Part cat"]}'}
    #             enriched_products.append(enriched_product)
    #             # print(enriched_product)
    #             found = True
    #             break

    # with open(f'{filePath}data files/product/products.json', 'w') as f:
    #     json.dump(enriched_products, f)


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


test()
# convert_to_json()
# enrich_products()
# generate_csv()
