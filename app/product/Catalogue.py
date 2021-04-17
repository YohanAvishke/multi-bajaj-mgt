from app.DataReader import *

file_path = '../../data/product/catalogue.csv'
field_names = ('Part Number', 'Quantity', 'Unit Price', 'Notes')
print(csv_to_json(file_path, field_names))
