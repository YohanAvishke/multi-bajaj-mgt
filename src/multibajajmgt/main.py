import os

import multibajajmgt.client.odoo.client as odoo_client
import multibajajmgt.client.dpmc.client as dpmc_client
import multibajajmgt.client.googlesheet.client as sheet_client
import multibajajmgt.invoice.dpmc as invoice_dpmc_service
import multibajajmgt.invoice.sale as invoice_sale_service
import multibajajmgt.invoice.thirdparty as invoice_tp_service
import multibajajmgt.product.service as product_service
import multibajajmgt.price.dpmc as price_dpmc_service
import multibajajmgt.price.thirdparty as price_tp_service
import multibajajmgt.stock.service as stock_service

from config import configure_app, configure_env
from logger import configure_logger
from multibajajmgt.enums import (
    POSParentCategory as Categ,
    QuantityAvailability as QtyAva
)

# Configure the logging level and format
configure_logger()

# Configure env variables
if not os.getenv("ENV_FLAG"):
    configure_env()

# Configure application execution details
app = configure_app(Categ.dpmc, QtyAva.all)

# Configure clients
odoo_client.configure()
dpmc_client.configure()
sheet_client.configure()

# Update dpmc prices
# price_dpmc_service.export_prices()
# price_dpmc_service.update_product_prices()
# price_dpmc_service.merge_historical_data()

# Adjustment from dpmc invoices
# invoice_dpmc_service.export_invoice_data()
# invoice_dpmc_service.export_products()
# stock_service.export_products()
# stock_service.create_adjustment()

# Adjustment from sales invoices
# invoice_sale_service.export_invoice_data()
# stock_service.export_products()
# stock_service.create_adjustment()

# Adjustment from third-party invoices
#   Setup
# invoice_tp_service.export_invoice_data()
#   Create products
# stock_service.export_products()
# product_service.create_missing_products()
#   Create adjustment
# stock_service.export_products()
# stock_service.create_adjustment()
#   Price update
# price_tp_service.export_prices()
# price_tp_service.update_product_prices()
