from multibajajmgt.enums import (
    DocumentResourceName as DocName,
    POSParentCategory as POSCateg,
    QuantityAvailability)


class FileHandler:
    _price_file = None
    _invoice_file = None
    _stock_file = None
    _adjustment_file = None
    _filenames = None

    def get_price(self):
        return self._price_file

    def set_price_file(self, price_file):
        self._price_file = price_file

    def get_invoice(self):
        return self._invoice_file

    def set_invoice_file(self, invoice_file):
        self._invoice_file = invoice_file

    def get_stock(self):
        return self._stock_file

    def set_stock_file(self, stock_file):
        self._stock_file = stock_file

    def get_adj(self):
        return self._adjustment_file

    def set_adjustment_file(self, adjustment_file):
        self._adjustment_file = adjustment_file

    def set_filenames(self, filenames):
        self._filenames = filenames
        self.set_price_file(filenames[0])
        self.set_invoice_file(filenames[1])
        self.set_stock_file(filenames[2])
        self.set_adjustment_file(filenames[3])

    def configure_files(self, pos_categ):
        all_filenames = [None, None, DocName.stock_all, None]
        dpmc_filenames = [DocName.price_dpmc_all, DocName.invoice_dpmc, DocName.stock_dpmc_all, DocName.adjustment_dpmc]
        sale_filenames = [None, DocName.invoice_sales, DocName.stock_all, DocName.adjustment_sales]
        tp_filenames = [DocName.price_tp, DocName.invoice_tp, DocName.stock_tp_all, DocName.adjustment_tp]
        if pos_categ == POSCateg.all:
            self.set_filenames(all_filenames)
        elif pos_categ == POSCateg.dpmc:
            self.set_filenames(dpmc_filenames)
        elif pos_categ == POSCateg.sales:
            self.set_filenames(sale_filenames)
        elif pos_categ == POSCateg.tp:
            self.set_filenames(tp_filenames)


class App:
    _instance = None
    _pos_categ: POSCateg = None
    _qty_limit: QuantityAvailability = None
    _file_handler: FileHandler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_app(cls):
        return cls._instance

    def get_pos_categ(self):
        return self._pos_categ

    def set_pos_categ(self, pos_categ):
        self._pos_categ = pos_categ
        self.set_file_handler(pos_categ)

    def get_qty_limit(self):
        return self._pos_categ

    def set_qty_limit(self, qty_limit):
        self._qty_limit = qty_limit

    def get_file_handler(self):
        return self._file_handler

    def set_file_handler(self, pos_categ):
        file_handler = FileHandler()
        file_handler.configure_files(pos_categ)
        self._file_handler = file_handler
