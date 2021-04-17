import csv
import json


def csv_to_json(file_path, field_names):
    catalogue_file = open(file_path, 'r')
    catalogue = []

    reader = csv.DictReader(catalogue_file, field_names)
    for idx, row in enumerate(reader):
        if idx != 0:
            catalogue.append(row)
    catalogue = json.dumps(catalogue, indent=4)

    return catalogue
