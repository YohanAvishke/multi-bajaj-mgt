class Product:
    def __init__(self, name, default_code, barcode = False, price = 0, image = False, categ_id = 1,
                 pos_categ_id = False):
        self.name = name
        self.default_code = default_code
        self.barcode = barcode
        self.price = price
        self.image = image
        self.categ_id = categ_id
        self.pos_categ_id = pos_categ_id
