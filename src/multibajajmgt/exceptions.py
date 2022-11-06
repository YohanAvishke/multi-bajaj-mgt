from requests.exceptions import *


class InvalidIdentityError(Exception):
    pass


class ProductCreationFailed(Exception):
    pass


class DataNotFoundError(RequestException):
    pass


class InvalidDataFormatReceived(RequestException):
    pass


class ProductRefExpired(DataNotFoundError):
    pass
