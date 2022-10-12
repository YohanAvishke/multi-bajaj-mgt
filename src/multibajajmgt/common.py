import errno
import json
import logging
import os
import time

from tabulate import tabulate

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


def drop_duplicates(df, key):
    """ Filter duplicates by a column and drop the found rows.

    :param df: pandas dataframe,
    :param key: string, column name
    :return: pandas dataframe,
    """
    df["is_duplicate"] = df.duplicated(subset = [key], keep = False)
    duplicate_df = df[df["is_duplicate"]]
    if duplicate_df.size > 0:
        log.warning(f"Filtering duplicates,\n {duplicate_df}")
        df = df.drop_duplicates(subset = ["res_id"], keep = "first")
    df = df.drop("is_duplicate", axis = 1)
    return df


def enrich_products_by_external_id(product_df, id_df):
    """ Add id dataframe to product dataframe.

    * Build external id.
    * Drop and rename columns.
    * Merge price list and external id list(by id).

    :param product_df: pandas dataframe, products
    :param id_df: pandas dataframe, ids
    :return: pandas dataframe, products merged with ids
    """
    # Build external id
    id_df["external_id"] = id_df[["module", "name"]].agg(".".join, axis = 1)
    # Drop and rename columns
    id_df = id_df \
        .drop(["id", "name", "module"], axis = 1) \
        .rename({"res_id": "id"}, axis = 1)
    # Merge price list and external id list(by id)
    enrich_price_df = id_df.merge(product_df, on = "id", how = "inner")
    return enrich_price_df
