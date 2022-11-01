import errno
import json
import os
import pandas as pd
import time

from io import StringIO
from loguru import logger as log
from tabulate import tabulate


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


def write_to_fwf(df, path, mode = "w"):
    """ Write function for Pandas "read_fwf". Working with fixed-width files.

    :param df: pandas dataframe, data to write
    :param path: string, path of the file to be saved
    :param mode: string, "w" to create and write, "a" to append to existing
    """
    log.debug(f"Saving fixed-width text file to {path}")
    content = tabulate(df.values.tolist(), list(df.columns), tablefmt = "plain")
    open(path, mode).write(content)


def get_dated_dir(base_path, date = time.time()):
    """ Get dir name depending on date(yyyy-mm-dd).

    :param base_path: string, base suffix path for dir
    :param date: int, timestamp use `time.mktime(datetime.datetime.strptime(2011-12-11, "%Y-%m-%d").timetuple())`
    :return: string, base combined with curr path
    """
    date = time.strftime("%Y-%m-%d", time.localtime(date))
    return f"{base_path}/{date}"


def get_now_file(file_extension, base_name = None):
    """ Get file name  depending on current time(hh-mm-ss).

    :param file_extension: string, files' extension type(eg: csv, json)
    :param base_name:  string, base suffix name for file
    :return: string, base combined with curr name
    """
    now_time = time.strftime("%H-%M-%S", time.localtime(time.time()))
    if base_name:
        return f"{base_name}_{now_time}.{file_extension}"
    return f"{now_time}.{file_extension}"


def mk_dir(dir_path, file_path):
    """ Create and return directory.

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


def csvstr_to_df(string):
    str_obj = StringIO(string)
    # noinspection PyTypeChecker
    df = pd.read_csv(str_obj)
    return df
