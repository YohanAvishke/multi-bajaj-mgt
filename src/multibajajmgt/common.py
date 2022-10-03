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


def get_curr_dir(base_path):
    """ Get dir name depending on current date(yyyy-mm-dd)

    :param base_path: string, base suffix path for dir
    :return: string, base combined with curr path
    """
    now_date = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    return f"{base_path}/{now_date}"


def get_now_file(file_extension, base_name = None):
    """ Get file name  depending on current time(hh-mm-ss

    :param file_extension: string, files' extension type(eg: csv, json)
    :param base_name:  string, base suffix name for file
    :return: string, base combined with curr name
    """
    now_time = time.strftime("%H-%M-%S", time.localtime(time.time()))
    if base_name:
        return f"{base_name}_{now_time}.{file_extension}"
    return f"{now_time}.{file_extension}"


def mk_historical(dir_path, file_path):
    """ Create historical directory

    :param dir_path: string, directory(date) path
    :param file_path: string, file(time) name
    :return: string, combination of dir path and file name
    """
    try:
        os.makedirs(dir_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
            pass
        else:
            raise
    return f"{dir_path}/{file_path}"
