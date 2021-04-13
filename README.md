# Multi Bajaj POS System
Scripts and Data files used for converting, formatting and enriching data persisted in the Odoo POS system.

# TODO
1. Create a script to update unit prices
   1. Send `CURL` requests with a buffer(5 sec) to retreive unit prices for a list of part numbers.
   2. Filter about 300 parts from `current_price.csv` and send 400 requests per day.
   3. Maybe break down the request into 100 packets per hour.
2. Check the discount in the stupid report(ERP) 
