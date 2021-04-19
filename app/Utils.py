import csv
import json
from collections import OrderedDict


def csv_to_json(file_path=None, field_names=None, data_obj=None):
    """
    data_obj  should be [OrderedDict(), ...]
    """
    objects = []

    if file_path is not None:
        file = open(file_path, 'r')
        data_obj = csv.DictReader(file, field_names)

    for idx, row in enumerate(data_obj):
        if idx != 0:
            objects.append(row)
    objects = json.dumps(objects, indent=4)
    objects = json.loads(objects)

    return objects

