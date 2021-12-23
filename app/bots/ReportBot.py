import pandas as pd

REPORT_PATH = "../../data/reports"

read_file = pd.read_excel(f"{REPORT_PATH}/pos.payment,unmerged.xlsx")
read_file.to_excel(f"{REPORT_PATH}/pos.payment,merged.xlsx")
