import os
import logging

from dotenv import find_dotenv, load_dotenv
from enums import (
    DocumentResourceName as DRName,
    DocumentResourceExtension as DSExt,
    EnvVariable
)
from multibajajmgt.app import App

LOG_LEVEL = logging.INFO

log = logging.getLogger(__name__)

# Paths
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SOURCE_DIR = f"{ROOT_DIR}/src/multibajajmgt"
DATA_DIR = f"{ROOT_DIR}/data"
RAW_DATA_DIR = f"{DATA_DIR}/.raw"
# Price
PRICE_DIR = f"{DATA_DIR}/price"
PRICE_BASE_DPMC_FILE = f"{PRICE_DIR}/{DRName.price_dpmc_all}.{DSExt.csv}"
PRICE_HISTORY_DIR = f"{PRICE_DIR}/history"
# Invoice
INVOICE_DIR = f"{DATA_DIR}/invoice"
INVOICE_RAW_FILE = f"{RAW_DATA_DIR}/{DRName.invoice_dpmc}.{DSExt.json}"
INVOICE_HISTORY_DIR = f"{INVOICE_DIR}/history"
# Stock
STOCK_DIR = f"{DATA_DIR}/stock"
ADJUSTMENT_DIR = f"{STOCK_DIR}/adjustments"


def configure_env():
    """ Configure environment variables
    """
    log.debug("Configuring environment variables.")
    load_dotenv(find_dotenv(f"{ROOT_DIR}/.env"))


ODOO_SERVER_URL = os.getenv(EnvVariable.odoo_server_url)
ODOO_SERVER_USERNAME = os.getenv(EnvVariable.odoo_server_username)
ODOO_SERVER_API_KEY = os.getenv(EnvVariable.odoo_server_api_key)
ODOO_DATABASE_NAME = os.getenv(EnvVariable.odoo_database_name)

DPMC_SERVER_URL = os.getenv(EnvVariable.dpmc_server_url)
DPMC_SERVER_USERNAME = os.getenv(EnvVariable.dpmc_server_username)
DPMC_SERVER_PASSWORD = os.getenv(EnvVariable.dpmc_server_password)
DPMC_SESSION_LIFETIME = 3600  # 1 hour

DATETIME_FORMAT = "%c"
DATETIME_FILE_FORMAT = "%Y-%m-%d_%H-%M-%S"


def configure_app(pos_categ, qty_limit):
    """ Configure application

    :param pos_categ: POSCategory string,
    :param qty_limit: QuantityAvailability string,
    :return: App object,
    """
    app = App()
    app.set_pos_categ(pos_categ)
    app.set_qty_limit(qty_limit)
    return app
