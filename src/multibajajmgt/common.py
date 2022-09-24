import logging
import json

log = logging.getLogger(__name__)


def write_to_csv(path, df, columns = None, headers = True):
    """Save data to a CSV file.

    :param path: file path
    :param df: dataframe object
    :param columns: columns that are been written
    :param headers: headers of the csv file
    """
    log.info(f"Saving CSV file to {path}")
    df.to_csv(path, columns = columns, header = headers, index = False)


def write_to_json(path, data):
    """Save data to JSON file.

    :param path: string, file path
    :param data: dictionary, json data
    """
    log.info(f"Saving JSON file to {path}")
    with open(path, "w") as file:
        json.dump(data, file)
