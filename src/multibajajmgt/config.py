import os
import logging

from dotenv import find_dotenv, load_dotenv
from enums import (
    DocumentResourceName as DRName,
    DocumentResourceExtension as DRExt,
    EnvVariable
)
from loguru import logger as log
from multibajajmgt.app import App

LOG_LEVEL = logging.DEBUG

# Paths
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SOURCE_DIR = f"{ROOT_DIR}/src/multibajajmgt"
DATA_DIR = f"{ROOT_DIR}/data"
# Price
PRICE_DIR = f"{DATA_DIR}/price"
PRICE_BASE_DPMC_FILE = f"{PRICE_DIR}/{DRName.price_dpmc_all}.{DRExt.csv}"
PRICE_BASE_TP_FILE = f"{PRICE_DIR}/{DRName.price_tp}.{DRExt.csv}"
PRICE_HISTORY_DIR = f"{PRICE_DIR}/history"
# Invoice
INVOICE_DIR = f"{DATA_DIR}/invoice"
INVOICE_DPMC_FILE = f"{INVOICE_DIR}/{DRName.invoice_dpmc}.{DRExt.json}"
INVOICE_TP_FILE = f"{INVOICE_DIR}/{DRName.invoice_tp}.{DRExt.txt}"
INVOICE_HISTORY_DIR = f"{INVOICE_DIR}/history"
# Stock
STOCK_DIR = f"{DATA_DIR}/stock"
STOCK_ALL_FILE = f"{STOCK_DIR}/{DRName.stock_all}.{DRExt.csv}"
ADJUSTMENT_DIR = f"{STOCK_DIR}/adjustments"
# Product
PRODUCT_DIR = f"{DATA_DIR}/product"
PRODUCT_TMPL_DIR = f"{PRODUCT_DIR}/templates"
PRODUCT_HISTORY_FILE = f"{PRODUCT_DIR}/product_history.csv"
# Sale
SALE_DIR = f"{DATA_DIR}/sale"


def configure_env():
    """ Configure environment variables.
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
    """ Configure application.

    :param pos_categ: POSCategory string,
    :param qty_limit: QuantityAvailability string,
    :return: App object,
    """
    app = App()
    app.set_pos_categ(pos_categ)
    app.set_qty_limit(qty_limit)
    return app
