import json
import csv

filePath = '/Users/yohanavishke/Documents/Projects/YohanAvishke/multi-bajaj-pos/data/'


def get_raw_category_data():
    with open(f'{filePath}inventory/categories.json') as jsonFile:
        return json.load(jsonFile)


def get_template():
    with open(f'{filePath}templates/product_categories.csv') as csv_file:
        csv_template = csv.reader(csv_file, delimiter=',')
        for row in csv_template:
            return row


def enrich_category():
    raw_categories = get_raw_category_data()

    with open(f'{filePath}inventory/categories.csv', mode='w') as csvFile:
        csv_writer = csv.writer(csvFile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(get_template())
        for raw_category in raw_categories:
            code, description, status = raw_category['Category Code'], \
                                        raw_category['Description'].title().replace(' ', ''), raw_category['Status']
            csv_writer.writerow(
                [f'point_of_sale.{code}', 'All / Saleable / PoS', description, f'All / Saleable / PoS / {description}',
                 f'All / Saleable / PoS / {description}'])


enrich_category()
