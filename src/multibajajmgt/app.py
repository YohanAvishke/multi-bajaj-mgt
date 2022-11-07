from multibajajmgt.client.odoo.client import fetch_all_stock, fetch_dpmc_stock, fetch_thirdparty_stock
from multibajajmgt.enums import (
    DocumentResourceName as DocName,
    POSParentCategory as POSCateg,
    QuantityAvailability)


class App:
    _instance = None
    _pos_categ: POSCateg = None
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

    def eval_stock_fetcher(self):
        if self._pos_categ == POSCateg.dpmc:
            return fetch_dpmc_stock
        elif self._pos_categ == POSCateg.tp:
            return fetch_thirdparty_stock
        else:
            return fetch_all_stock

    def eval_file_names(self):
        """ Evaluate file names for the matching application

        :return: list, [price, invoice, stock, adjustment]
        """
        all_filenames = [None, None, DocName.stock_all, None]
        dpmc_filenames = [DocName.price_dpmc_all, DocName.invoice_dpmc, DocName.stock_dpmc_all, DocName.adjustment_dpmc]
        sale_filenames = [None, DocName.invoice_sales, DocName.stock_all, DocName.adjustment_sales]
        tp_filenames = [DocName.price_tp, DocName.invoice_tp, DocName.stock_tp_all, DocName.adjustment_tp]
        if self._pos_categ == POSCateg.all:
            return all_filenames
        elif self._pos_categ == POSCateg.dpmc:
            return dpmc_filenames
        elif self._pos_categ == POSCateg.sales:
            return sale_filenames
        elif self._pos_categ == POSCateg.tp:
            return tp_filenames
