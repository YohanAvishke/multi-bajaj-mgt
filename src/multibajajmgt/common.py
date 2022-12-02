import errno
import json
import os
import sys
import time

import pandas as pd

from io import StringIO
from loguru import logger as log
from multibajajmgt.app import App


def write_to_csv(path, df, mode = "w", columns = None, header = True):
    """ Save data to a CSV file.

    :param mode: str, `w` to write, `a` to append.
    :param path: str, file path.
    :param df: pandas dataframe, data to be written.
    :param columns: None/list, columns of the csv data.
    :param header: True/list, header of the csv file.
    """
    log.debug("Save CSV file to {}.", path)
    df.to_csv(path, mode = mode, columns = columns, header = header, index = False)


def write_to_json(path, data):
    """ Save data to a JSON file.

    :param path: string, file path.
    :param data: dict, data.
    """
    log.debug("Save JSON file to {}.", path)
    with open(path, "w") as file:
        json.dump(data, file)


def get_dated_dir(base_path, date = time.time()):
    """ Get Dir named by the current date (yyyy-mm-dd).

    :param base_path: str, base suffix path for dir.
    :param date: int, timestamp formed by `time.mktime(datetime.datetime.strptime(2011-12-11, "%Y-%m-%d").timetuple())`.
    :return: str, base + curr dir path.
    """
    log.debug("Get a dated directory for base path: {}.", base_path)
    date = time.strftime("%Y-%m-%d", time.localtime(date))
    return f"{base_path}/{date}"


def get_now_file(file_extension, base_name = None):
    """ Get file named by current time (hh-mm-ss).

    :param file_extension: str, a file extension type (eg: csv, json).
    :param base_name:  str, base suffix name for file.
    :return: str, base + curr file name.
    """
    log.debug("Get a now file for base name: {} and extension: {}.", base_name, file_extension)
    now_time = time.strftime("%H-%M-%S", time.localtime(time.time()))
    if base_name:
        return f"{base_name}_{now_time}.{file_extension}"
    return f"{now_time}.{file_extension}"


def mk_dir(dir_path, file_path):
    """ Create and get the directory's name.

    :param dir_path: str, directory path.
    :param file_path: str, file name.
    :return: str, dir_path + file_path.
    """
    log.debug("Create dir for: {} (if doesn't exist), and get file path.", dir_path)
    try:
        os.makedirs(dir_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(dir_path):
            pass
        else:
            log.critical("Failed to retrieve existing dir: {}", dir_path)
            sys.exit(0)
    return f"{dir_path}/{file_path}"


def csvstr_to_df(string):
    """ Convert CSV String to Dataframe.

    :param string: str, valid CSV string.
    :return: pandas dataframe, converted dataframe.
    """
    log.debug("Convert a CSV supported String to a Dataframe.")
    str_obj = StringIO(string)
    # noinspection PyTypeChecker
    df = pd.read_csv(str_obj)
    return df


def get_files():
    """ Get the filehandler to find corresponding file names for exporting/importing data.

    :return: list, of file names.
    """
    log.debug("Retrieve the file handler.")
    return App.get_app().get_file_handler()
