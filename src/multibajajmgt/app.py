import logging

from multibajajmgt.enums import POSParentCategory, QuantityAvailability

log = logging.getLogger(__name__)


class App:
    _instance = None
    _pos_categ: POSParentCategory = None
    _qty_limit: QuantityAvailability = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(App, cls).__new__(cls)
        return cls._instance

    def get_pos_categ(self):
        return self._pos_categ

    def set_pos_categ(self, pos_categ):
        self._pos_categ = pos_categ

    def get_qty_limit(self):
        return self._pos_categ

    def set_qty_limit(self, qty_limit):
        self._qty_limit = qty_limit
