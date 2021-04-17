import json

with open('catalogue.json') as f:
    data = json.load(f)

parts = {}
duplicates = []

# for part in data:
#     code, description, cat, serial, hier, moq = part['Part Code'], part['Description'], part['Part cat'], \
#                                                 part['Serial Base'], part['Pro Hier Code'], part['MOQ Value']
#     if code in parts.keys():
#         duplicates.append(code)
#     parts[code] = {description, cat, serial, hier, moq}

print(len(data))
# print(len(duplicates))
# print(parts)

# 519 duplicates on parts codes with different hier codes
# duplicates on parts codes with a LP prefix
