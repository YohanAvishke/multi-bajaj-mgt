import csv
import logging
from datetime import date

# -*- File Paths -*-
BARCODE_NOMENCLATURE_PATH = "../data/product/product.barcode.csv"
INVENTORY_ODOO_PATH = "../data/inventory/product.bajaj.inventory.csv"

# -*- Main function -*-
if __name__ == "__main__":
    logging_format = "%(asctime)s: %(levelname)s - %(message)s"
    logging.basicConfig(format = logging_format, level = logging.INFO, datefmt = "%H:%M:%S")


def setup_barcodes():
    headers = ("Barcode Nomenclature", "Rules/Rule Name", "Rules/Type", "Rules/Alias", "Rules/Barcode Pattern",
               "Rules/Sequence")

    with open(INVENTORY_ODOO_PATH, "r") as inventory_file:
        inventory = list(csv.DictReader(inventory_file))

    with open(BARCODE_NOMENCLATURE_PATH, mode = 'w') as barcode_file:
        barcode_writer = csv.DictWriter(barcode_file, fieldnames = headers)
        barcode_writer.writeheader()

        for idx, product in enumerate(inventory):
            product_number = product["Internal Reference"]
            if idx == 0:
                barcode_writer.writerow(
                    {"Barcode Nomenclature": f"DPMC Nomenclature - {date.today()}", "Rules/Rule Name": product_number,
                     "Rules/Type": "Alias", "Rules/Alias": product_number,
                     "Rules/Barcode Pattern": f"{product_number}-{{N}}", "Rules/Sequence": "1"})
                continue
            barcode_writer.writerow(
                {"Barcode Nomenclature": "", "Rules/Rule Name": product_number, "Rules/Type": "Alias",
                 "Rules/Alias": product_number, "Rules/Barcode Pattern": f"{product_number}-{{N}}",
                 "Rules/Sequence": "1"})

        barcode_writer.writerow(
            {"Barcode Nomenclature": "", "Rules/Rule Name": "All Products", "Rules/Type": "Unit Product",
             "Rules/Alias": "0", "Rules/Barcode Pattern": ".*", "Rules/Sequence": "2"})

    logging.info("Barcode creation completed")


setup_barcodes()
