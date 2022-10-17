import logging

from multibajajmgt.enums import POSCategory, QuantityAvailability

log = logging.getLogger(__name__)


class App:
    _pos_categ: POSCategory = POSCategory.all
    _qty_limit: QuantityAvailability = QuantityAvailability.all

    def __init__(self, pos_categ, qty_limit):
        self._pos_categ = pos_categ
        self._qty_type = qty_limit

    def get_pos_categ(self):
        return self._pos_categ

    def set_pos_categ(self, pos_categ):
        self._pos_categ = pos_categ

    def get_qty_limit(self):
        return self._pos_categ

    def set_qty_limit(self, qty_limit):
        self._qty_limit = qty_limit
