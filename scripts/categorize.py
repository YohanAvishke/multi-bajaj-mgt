import json

with open('../data/inventory/full_catalogue.json') as f:
    global_parts = json.load(f)
with open('../data/inventory/price_list_10-02-2021.json') as f:
    local_parts = json.load(f)
with open('../data/inventory/categories.json') as f:
    categories = json.load(f)

for idx,local_part in enumerate(local_parts):
	for global_part in global_parts:
		if local_part['Part Code'] == global_part['Part Code']:
			local_part['Category Code'] = global_part['Part cat']
			
			for category in categories:
				if local_part['Category Code'] == category['Category Code']:
					local_part['Category Description'] = category['Description']
					break

			print(idx)
			break

with open('../data/inventory/store_catalogue_10-02-2021.json', 'w') as store_catalogue:
    json.dump(local_parts, store_catalogue)