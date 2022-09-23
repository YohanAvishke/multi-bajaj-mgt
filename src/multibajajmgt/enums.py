from enum import Enum


class MultiBajajMgtEnum(str, Enum):
    def __str__(self) -> str:
        return str.__str__(self)


class EnvVariable(MultiBajajMgtEnum):
    server_url = "SERVER_URL"
    server_api_key = "SERVER_API_KEY"
    database_name = "DATABASE_NAME"
    server_username = "SERVER_USERNAME"


class DocumentResourceType(MultiBajajMgtEnum):
    price_dpmc_all = "price-dpmc-all.csv"


class OdooFieldName(MultiBajajMgtEnum):
    external_id = "External ID"
    internal_id = "Internal Reference"
    sales_price = "Sales Price"
    cost = "Cost"
