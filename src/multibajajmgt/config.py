import logging
import os

from dotenv import find_dotenv, load_dotenv
from enums import EnvVariable
from loguru import logger as log
from multibajajmgt.app import App

LOG_LEVEL = logging.INFO

# Paths
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SOURCE_DIR = f"{ROOT_DIR}/src/multibajajmgt"
DATA_DIR = f"{ROOT_DIR}/data"
# Price
PRICE_DIR = f"{DATA_DIR}/price"
PRICE_HISTORY_DIR = f"{PRICE_DIR}/history"
# Invoice
INVOICE_DIR = f"{DATA_DIR}/invoice"
INVOICE_HISTORY_DIR = f"{INVOICE_DIR}/history"
# Stock
STOCK_DIR = f"{DATA_DIR}/stock"
ADJUSTMENT_DIR = f"{STOCK_DIR}/adjustments"
# Product
PRODUCT_DIR = f"{DATA_DIR}/product"
PRODUCT_TMPL_DIR = f"{PRODUCT_DIR}/templates"
# Sale
SALE_DIR = f"{DATA_DIR}/sale"


def configure_env():
    """ Configure Environment variables.
    """
    log.debug("Configure Environment variables.")
    load_dotenv(find_dotenv(f"{ROOT_DIR}/.env"))


# odoo specific configurations
ODOO_SERVER_URL = os.getenv(EnvVariable.odoo_server_url)
ODOO_SERVER_USERNAME = os.getenv(EnvVariable.odoo_server_username)
ODOO_SERVER_API_KEY = os.getenv(EnvVariable.odoo_server_api_key)
ODOO_DATABASE_NAME = os.getenv(EnvVariable.odoo_database_name)
# dpmc specific configurations
DPMC_SERVER_URL = os.getenv(EnvVariable.dpmc_server_url)
DPMC_SERVER_USERNAME = os.getenv(EnvVariable.dpmc_server_username)
DPMC_SERVER_PASSWORD = os.getenv(EnvVariable.dpmc_server_password)
DPMC_SESSION_LIFETIME = 3600  # 1 hour
# date time based configurations
DATETIME_FORMAT = "%c"
DATETIME_FILE_FORMAT = "%Y-%m-%d_%H-%M-%S"


def configure_app(pos_categ, qty_limit):
    """ Configure application.

    :param pos_categ: str,
    :param qty_limit: str,
    :return: app,
    """
    log.debug("Setup application.")
    app = App()
    app.set_pos_categ(pos_categ)
    app.set_qty_limit(qty_limit)
    return app
