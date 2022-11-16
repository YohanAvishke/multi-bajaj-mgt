from requests.exceptions import *


class InvalidIdentityError(Exception):
    pass


class DataNotFoundError(RequestException):
    pass


class InvalidDataFormatReceived(RequestException):
    pass


class ProductRefExpired(DataNotFoundError):
    pass


# Product Exceptions
class ProductInitException(Exception):
    pass


class ProductInquiryException(Exception):
    pass
