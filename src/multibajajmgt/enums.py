from enum import Enum


class MultiBajajMgtEnum(str, Enum):
    def __str__(self) -> str:
        return str.__str__(self)


class EnvVariable(MultiBajajMgtEnum):
    odoo_server_url = "ODOO_SERVER_URL"
    odoo_server_api_key = "ODOO_SERVER_API_KEY"
    odoo_database_name = "ODOO_DATABASE_NAME"
    odoo_server_username = "ODOO_SERVER_USERNAME"
    dpmc_server_url = "DPMC_SERVER_URL"
    dpmc_server_username = "DPMC_SERVER_SERVER_USERNAME"
    dpmc_server_password = "DPMC_SERVER_PASSWORD"


class DocumentResourceType(MultiBajajMgtEnum):
    price_dpmc_all = "price-dpmc-all.csv"


class OdooFieldName(MultiBajajMgtEnum):
    external_id = "External ID"
    internal_id = "Internal Reference"
    sales_price = "Sales Price"
    cost = "Cost"
