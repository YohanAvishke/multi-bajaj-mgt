import os
import logging
import xmlrpc.client

from dotenv import find_dotenv, load_dotenv
from enums import EnvVariable

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
LOG_LEVEL = logging.DEBUG

log = logging.getLogger(__name__)


def configure_env():
    load_dotenv(find_dotenv(f"{ROOT_DIR}/.env"))


SERVER_URL = os.getenv(EnvVariable.server_url)
SERVER_USERNAME = os.getenv(EnvVariable.server_username)
SERVER_API_KEY = os.getenv(EnvVariable.server_api_key)
DATABASE_NAME = os.getenv(EnvVariable.database_name)


def configure_odoo_client():
    log.debug("Configuring odoo-client by setting up the user-id")
    common = xmlrpc.client.ServerProxy(f"{SERVER_URL}/xmlrpc/2/common")
    return common.authenticate(DATABASE_NAME, SERVER_USERNAME, SERVER_API_KEY, {})
