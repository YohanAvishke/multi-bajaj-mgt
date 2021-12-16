from __future__ import print_function, unicode_literals

from app.config import ROOT_DIR

import pandas as pd

INVOICE_NISHAN_FILE = f"{ROOT_DIR}/data/invoice/nishan.txt"
INVOICE_NISHAN_FILE_2 = f"{ROOT_DIR}/data/invoice/nishan.csv"


def main():
    all_capitals = ['4s', '5p', 'ct', 'cdi', 'dh', 'dz', 'jk', 'lh', 'nd', 'nm', 'ns', 'rh', 'ug']

    with open(INVOICE_NISHAN_FILE) as file:
        lines = file.readlines()

    products = []
    for line in lines:
        words = line.split(" ")

        product = {
            "Name": " ".join(words[1:-3]).title(),
            "PartNumber": words[-3],
            "Quantity": words[-2],
            "Price": words[-1].replace(",", "")
            }
        products.append(product)

        # index = words[0]
        # amount = words[-1].replace("\n", "")
        # price = words[-2]
        # quantity = words[-3]
        # part_number = words[-4]
        # name = ""
        # for word in words[1:-4]:
        #     if word.lower() in all_capitals:
        #         name += f' {word.upper()}'
        #     else:
        #         name += f' {word.title()}'
        # name = " ".join(words[1:-4])

    products_df = pd.DataFrame(products)
    products_df.to_csv(INVOICE_NISHAN_FILE_2, header = ['Name', 'PartNumber', 'Quantity', 'Price'],
                       index = False)


if __name__ == '__main__':
    main()
