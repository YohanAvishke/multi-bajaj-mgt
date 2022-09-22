import logging

log = logging.getLogger(__name__)


def write_to_csv(path, df, columns, headers):
    df.to_csv(path, columns = columns, header = headers, index = False)
