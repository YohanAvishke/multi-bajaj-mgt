import os
import logging

import multibajajmgt.clients.odoo.client as odoo_client
import multibajajmgt.clients.dpmc.client as dpmc_client
import multibajajmgt.price.service as price_service

from logger import configure_logging
from config import configure_env

log = logging.getLogger(__name__)

# configure the logging level and format
configure_logging()

# configure env variables
if not os.getenv("ENV_FLAG"):
    configure_env()

# configure clients
# odoo_client.configure()
dpmc_client.configure()

# price_service.export_all_dpmc_products()
price_service.update_dpmc_product_prices()