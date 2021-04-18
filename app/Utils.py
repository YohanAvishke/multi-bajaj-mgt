import csv
import json


def csv_to_json(file_path=None, field_names=None, data_obj=None):
    """
    data_obj  should be [OrderedDict(), ...]
    """
    catalogue = []

    if file_path is not None:
        catalogue_file = open(file_path, 'r')
        data_obj = csv.DictReader(catalogue_file, field_names)

    for idx, row in enumerate(data_obj):
        if idx != 0:
            catalogue.append(row)
    catalogue = json.dumps(catalogue, indent=4)
    catalogue = json.loads(catalogue)

    return catalogue
