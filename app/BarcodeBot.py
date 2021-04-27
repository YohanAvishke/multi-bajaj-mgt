import csv
import json

HEADERS = ("Barcode Nomenclature", "Rules/Rule Name", "Rules/Type", "Rules/Alias", "Rules/Barcode Pattern", "Rules/Sequence")
BARCODE_NOMENCLATURE_PATH = "../data/product/barcode-nomenclature.csv"
INVENTORY_ODOO_PATH = "../data/product/adjustments/stock.inventory.line.csv"

def setup_barcodes():
	with open(INVENTORY_ODOO_PATH, "r") as inventory_file:
		inventory = list(csv.DictReader(inventory_file))

	with open(BARCODE_NOMENCLATURE_PATH, mode='w') as barcode_file:
	    barcode_writer = csv.DictWriter(barcode_file, fieldnames=HEADERS)

	    barcode_writer.writeheader()

	    for idx, product in enumerate(inventory):
	    	product_number = product["Product/Internal Reference"]
	    	if idx == 0:
	    		barcode_writer.writerow({"Barcode Nomenclature": "DPMC barcodes", "Rules/Rule Name": product_number, "Rules/Type": "Alias", 
	    			"Rules/Alias": product_number, "Rules/Barcode Pattern": f"{product_number}-1", "Rules/Sequence": "1"})
	    		continue
	    	barcode_writer.writerow({"Barcode Nomenclature": "", "Rules/Rule Name": product_number, "Rules/Type": "Alias", 
	    			"Rules/Alias": product_number, "Rules/Barcode Pattern": f"{product_number}-1", "Rules/Sequence": "1"})

	    barcode_writer.writerow({"Barcode Nomenclature": "", "Rules/Rule Name": "All Products", "Rules/Type": "Unit Product", 
	    	"Rules/Alias": "0", "Rules/Barcode Pattern": ".*", "Rules/Sequence": "2"})

setup_barcodes()