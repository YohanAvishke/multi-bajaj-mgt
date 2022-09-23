import logging

log = logging.getLogger(__name__)


def write_to_csv(path, df, columns, headers):
    """
    Save data to a csv file
    :param path: file path
    :param df: dataframe object
    :param columns: columns that are been written
    :param headers: headers of the csv file
    """
    log.info(f"Saving csv file to {path}")
    df.to_csv(path, columns = columns, header = headers, index = False)
