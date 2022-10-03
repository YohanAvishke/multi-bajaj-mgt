import errno
import json
import logging
import os
import time

log = logging.getLogger(__name__)


def write_to_csv(path, df, mode = "w", columns = None, header = True):
    """ Save data to a CSV file.

    :param header:
    :param mode:
    :param path: file path
    :param df: dataframe object
    :param columns: columns that are been written
    :param header: headers of the csv file
    """
    log.debug(f"Saving CSV file to {path}")
    df.to_csv(path, mode = mode, columns = columns, header = header, index = False)


def write_to_json(path, data):
    """ Save data to JSON file.

    :param path: string, file path
    :param data: dictionary, json data
    """
    log.debug(f"Saving JSON file to {path}")
    with open(path, "w") as file:
        json.dump(data, file)


def mkdir_p(path):
    """ Create a directory

    :param path: string, path of the dir
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_filename_curr_date(dir_path, extension, base_name = None):
    """ Used for historical files. Create dir for date and get file name for time

    Current Date(directory)
        - Current time(file)
        - ...

    :param dir_path: string, place for the files to be created
    :param extension: string, files' extension type(eg: csv, json)
    :param base_name: string, base name(id) for each file name
    :return: string, file path
    """
    now_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    now_time = time.strftime("%H-%M-%S", time.localtime(time.time()))
    dir_path = f"{dir_path}/{now_date}"
    mkdir_p(dir_path)
    if base_name:
        return f"{dir_path}/{base_name}_{now_time}.{extension}"
    return f"{dir_path}/{now_time}.{extension}"
