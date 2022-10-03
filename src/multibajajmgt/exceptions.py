from requests.exceptions import *


class InvalidIdentityError(Exception):
    pass


class DataNotFoundError(RequestException):
    pass


class ProductRefExpired(DataNotFoundError):
    pass
