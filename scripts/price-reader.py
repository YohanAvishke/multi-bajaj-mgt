import requests
import json

url = "https://erp.dpg.lk/PADEALER/PADLRItemInquiry/Inquire"

headers = {
  'authority': 'erp.dpg.lk',
  'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
  'accept': '*/*',
  'x-requested-with': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
  'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'origin': 'https://erp.dpg.lk',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
  'accept-language': 'en-US,en;q=0.9',
  'cookie': '.AspNetCore.Session=CfDJ8GOndye%2Bf05JhuhX8EajvZbH94vjbEK5H8ZCwsuxHh68%2FYwV2%2FKi0dA%2FTmz3dpt6VzyaBNMAoElmRT%2BbnkqHMMPgyXYkG%2BhzTi0OSIeGceu9%2FaWZD5ddF%2FHzwLMx6hE04wmLMKSMNJUXh6U8XXB9Sz5qO9YawixjrG6n7R9XKt1V; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8GOndye-f05JhuhX8EajvZb8OXIKsLSsbSTWzYD3WNvO3OvX_Xuyl6YJ46d5VqtV4JUPfuTAIdPCeSmCK1QIhBC03-G_aOGFkfP4fKjw9FnGeSKESkSAi061F_kVE2IJ_xWtLiAXFV3qIJ9Std1WEKM'
}

numbers = [
'36BA4009',
'30161158',
'DH161066',
'AZ161001',
'DK191013',
'JM191012',
'AA191063',
'AA191117',
'JD561204',
'36JE0005',
'36PD0055',
'36DH4027',
'36JZ0121',
'36JY0103',
'36DK0074',
'36DH4117',
'36JH0004',
'36JU0002',
'36PF0086',
'36JH0033',
'31101041',
'36JA0020',
'28101118',
'39103519',
'39201719',
'36AA1004',
'JA511012',
'JE511038',
'JE511022',
'36241010',
'36102401',
'JY511012',
'JD511010',
'24181046'
]

for number in numbers:
	payload=f'strPartNo_PAItemInq={number}&strFuncType=INVENTORYDATA&strPADealerCode_PAItemInq=AC2011063676&STR_FORM_ID=00602&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&STR_INSTANT=DLR&STR_APP_ID=00011'
	
	response = requests.request("POST", url, headers=headers, data=payload)

	print(json.loads(response.text)['DATA']['dblSellingPrice'])



# curl 'https://erp.dpg.lk/PADEALER/PADLRItemInquiry/Inquire' \
#   -H 'authority: erp.dpg.lk' \
#   -H 'sec-ch-ua: "Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"' \
#   -H 'accept: */*' \
#   -H 'x-requested-with: XMLHttpRequest' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36' \
#   -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
#   -H 'origin: https://erp.dpg.lk' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'referer: https://erp.dpg.lk/Application/Home/PADEALER' \
#   -H 'accept-language: en-US,en;q=0.9' \
#   -H 'cookie: .AspNetCore.Session=CfDJ8GOndye%2Bf05JhuhX8EajvZbH94vjbEK5H8ZCwsuxHh68%2FYwV2%2FKi0dA%2FTmz3dpt6VzyaBNMAoElmRT%2BbnkqHMMPgyXYkG%2BhzTi0OSIeGceu9%2FaWZD5ddF%2FHzwLMx6hE04wmLMKSMNJUXh6U8XXB9Sz5qO9YawixjrG6n7R9XKt1V; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8GOndye-f05JhuhX8EajvZb8OXIKsLSsbSTWzYD3WNvO3OvX_Xuyl6YJ46d5VqtV4JUPfuTAIdPCeSmCK1QIhBC03-G_aOGFkfP4fKjw9FnGeSKESkSAi061F_kVE2IJ_xWtLiAXFV3qIJ9Std1WEKM' \
#   --data-raw 'strPartNo_PAItemInq=AP201130&strFuncType=INVENTORYDATA&strPADealerCode_PAItemInq=AC2011063676&STR_FORM_ID=00602&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&STR_INSTANT=DLR&STR_APP_ID=00011' \
#   --compressed