from scripts.DataReader import *

# csvfile = open('../data/inventory/price_list_10-02-2021..csv', 'r')
# jsonfile = open('../data/inventory/price_list_10-02-2021.json', 'w')
#
# fieldnames = ('Part Code','Description','PR Code','Price')
# reader = csv.DictReader( csvfile, fieldnames)
#
# jsonfile.write('[')
# for idx,row in enumerate(reader):
# 	if idx != 0:
# 		desc = row['Description']
# 		price = row['Price']
#
# 		desc = desc.replace('\n', '')
# 		if desc[-1] == ' ':
# 			desc = desc[:-1]
# 		row['Description'] = desc
#
# 		price = int(price.replace(',',''))
# 		row['Price'] = price
#
# 		json.dump(row, jsonfile)
# 		jsonfile.write(',\n')
#
# jsonfile.write(']')

file_path = '../data/product/catalogue.csv'
field_names = ('Part Number', 'Quantity', 'Unit Price', 'Notes')
print(csv_to_json(file_path, field_names))