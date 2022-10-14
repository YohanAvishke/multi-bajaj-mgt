from enum import Enum


class MultiBajajMgtStrEnum(str, Enum):
    def __str__(self) -> str:
        return str.__str__(self)


class MultiBajajMgtTupleEnum(Enum):
    pass


class EnvVariable(MultiBajajMgtStrEnum):
    odoo_server_url = "ODOO_SERVER_URL"
    odoo_server_api_key = "ODOO_SERVER_API_KEY"
    odoo_database_name = "ODOO_DATABASE_NAME"
    odoo_server_username = "ODOO_SERVER_USERNAME"
    dpmc_server_url = "DPMC_SERVER_URL"
    dpmc_server_username = "DPMC_SERVER_SERVER_USERNAME"
    dpmc_server_password = "DPMC_SERVER_PASSWORD"


class DocumentResourceExtension(MultiBajajMgtStrEnum):
    json = "json"
    csv = "csv"


class DocumentResourceType(MultiBajajMgtStrEnum):
    price_dpmc_all = "price_dpmc_all"
    invoice_dpmc = "invoice_dpmc"
    stock_dpmc_all = "stock_dpmc_all"
    adjustment_dpmc = "adjustment_dpmc"


class OdooCSVFieldName(MultiBajajMgtStrEnum):
    # Product
    external_id = "External ID"
    internal_id = "Internal Reference"
    sales_price = "Sales Price"
    cost = "Cost"
    qty_available = "Quantity On Hand"
    # Adjustment
    adj_name = "name"
    adj_acc_date = "Accounting Date"
    is_exh_products = "Include Exhausted Products"
    adj_prod_external_id = "line_ids / product_id / id"
    adj_loc_id = "line_ids / location_id / id"
    adj_prod_counted_qty = "line_ids / product_qty"


class OdooDBFieldName(MultiBajajMgtStrEnum):
    id = "id"
    res_id = "res_id"
    external_id = "external_id"
    internal_id = "default_code"
    sales_price = "list_price"
    cost = "standard_price"
    qty_available = "qty_available"


class ProductPriceStatus(MultiBajajMgtStrEnum):
    none = "none"
    up = "up"
    down = "down"
    equal = "equal"


class DPMCFieldName(MultiBajajMgtTupleEnum):
    def __init__(self, grn, order):
        self.grn = grn
        self.order = order

    part_code = ("STR_PART_CODE", "STR_PART_NO")
    part_desc = ("STR_DESC", "STR_DESC")
    part_qty = ("INT_QUANTITY", "INT_QUATITY")
    unit_cost = ("INT_UNIT_COST", "INT_UNIT_PRICE")
    total = ("INT_TOTAL_PART_COST", "INT_TOTAL_VALUE")
    ware_code = ("WAREHOUSE_CODE", "STR_WAREHOUSE_HIER")
    loc_code = ("LOCATION_CODE", None)
    rack_code = ("RACK_CODE", None)
    bin_code = ("BIN_CODE", None)
    sbin_code = ("SUBBIN_CODE", None)
    serial_base = ("STR_SERIAL_BASE", "STR_SERIAL_STATUS")


class InvoiceStatus(MultiBajajMgtStrEnum):
    failed = "Failed"
    success = "Success"
    multiple = "Multiple"


class InvoiceType(MultiBajajMgtTupleEnum):
    def __init__(self, val, col):
        self.val = val
        self.col = col

    invoice = ("Invoice", "STR_INVOICE_NO")
    mobile = ("Mobile", "STR_MOBILE_INVOICE_NO")


class InvoiceJSONFieldName(MultiBajajMgtStrEnum):
    # Invoice
    date = "Date"
    default_id = "Default ID"
    status = "Status"
    type = "Type"
    grn_id = "GRN ID"
    invoice_id = "Invoice ID"
    order_id = "Order ID"
    # Product
    products = "Products"
    part_code = "ID"
    part_desc = "Name"
    part_qty = "Quantity"
    unit_cost = "Unit Cost"
    total = "Total"
