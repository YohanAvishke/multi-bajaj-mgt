import os
import logging

from dotenv import find_dotenv, load_dotenv
from enums import EnvVariable

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
SOURCE_DIR = f"{ROOT_DIR}/src/multibajajmgt"
DATA_DIR = f"{ROOT_DIR}/data"

LOG_LEVEL = logging.INFO

log = logging.getLogger(__name__)


def configure_env():
    """Configure environment variables
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
DPMC_SESSION_LIFETIME = 5400  # 1 and 1/2 hours

DATETIME_FORMAT = "%c"
DATETIME_FILE_FORMAT = "%Y-%m-%d_%H-%M-%S"
