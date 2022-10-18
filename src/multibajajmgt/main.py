import os
import logging

import multibajajmgt.clients.odoo.client as odoo_client
import multibajajmgt.clients.dpmc.client as dpmc_client
import multibajajmgt.clients.googlesheet.client as sheet_client
import multibajajmgt.price.service as price_service
import multibajajmgt.stock.service as stock_service
import multibajajmgt.invoice.dpmc as invoice_dpmc_service
import multibajajmgt.invoice.sheetsale as invoice_sale_service

from config import configure_app, configure_env
from logger import configure_logging
from multibajajmgt.enums import (
    POSCategory as Categ,
    QuantityAvailability as QtyAva
)

log = logging.getLogger(__name__)

# Configure the logging level and format
configure_logging()

# Configure env variables
if not os.getenv("ENV_FLAG"):
    configure_env()

# Configure application execution details
# configure_app(Categ.dpmc, QtyAva.all)

# Configure clients
# odoo_client.configure()
# dpmc_client.configure()
sheet_client.configure()

# Update dpmc prices
# price_service.export_all_products()
# price_service.update_product_prices()
# price_service.merge_historical_data()

# Update from dpmc invoices
# stock_service.export_all_products()
# invoice_dpmc_service.fetch_invoice_data()
# invoice_dpmc_service.fetch_products()
# stock_service.create_adjustment()

# Update from sales invoices
# stock_service.export_all_products()
invoice_sale_service.fetch_invoice_data()
