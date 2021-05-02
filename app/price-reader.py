import requests
import json
import time

url = "https://erp.dpg.lk/PADEALER/PADLRItemInquiry/Inquire"

headers = {
    'authority': 'erp.dpg.lk',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'accept': '*/*',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                  '89.0.4389.114 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://erp.dpg.lk',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://erp.dpg.lk/Application/Home/PADEALER',
    'accept-language': 'en-US,en;q=0.9',
    'cookie': '.AspNetCore.Session=CfDJ8N8gIs%2FXx8JIrXltjeQ28vFI9s%2F8wmJ643e2fNePr7we7AemM0wbkub3WyXT2IYsn3sIOP%2F02eKCF8toZlaCtGxu%2FV9Yop4w9B90m%2BpCaUBQ2vt4zBZwljqEqMx7Otspc8QL%2FixZTN5Y1v4hkztinn0PCzQ8bwr3wLI8tMPW4g8h; .AspNetCore.Antiforgery.mEZFPqlrlZ8=CfDJ8N8gIs_Xx8JIrXltjeQ28vHKrxQ5gC2_4GrCt0RQDQmTVay0r_yc8Vsp1Pqx4kmdA1Cv6mpPE3SsC6NZZ96XZvoj4iRafCp2Nz_RJDrDUYG5oUKZckaDPTuVIJI0d2otNskc_muerV7Rb7O5Hy7aRb8'
}

numbers = [
'24140112',
'SAVNAA111085A',
'24100805',
'BA132171',
'PNBBA132174',
'BA132173',
'BA132172',
'AE101015',
'GKAE1001',
'GKAE1002',
'AA111095',
'AL241285',
'GK36AE00',
'AA171006',
'06101007',
'AE101006',
'52AB0098',
'DU101190',
'AZ621019',
'24161149',
'DS191013',
'JA531011',
'DS109905',
'DS101036',
'AE101014',
'AE101016',
'DH171013',
'BA123171',
'AA161215',
'52244040',
'BB121029',
'35101059',
'AA201185',
'AN101012',
'AN101328',
'22171007',
'24171024',
'AA101565',
'AN101166',
'AA101162',
'DH101484',
'DX101054',
'AB171003',
'AA111091',
'DJ191023',
'36AA4032',
'36DH4041',
'24101056',
'AA201041',
'AA101624',
'AN101308',
'AL201012',
'AZ161000',
'AA171006',
'DH111012',
'06101213',
'AA101364',
'06101007',
'24101177',
'AZ351002',
'06100702',
'AA111031',
'JA541019',
'CD101008',
'DS101336',
'24191019',
'36311014',
'36DK0005',
'36DU1504',
'36JA0002',
'36JZ0003',
'39105315',
'39193815',
'39214124',
'52Jl0066',
'AA101013',
'AA101392',
'PA151014',
'DG141019',
'DH181022',
'DJ151077',
'DJ201035',
'DL191014',
'DM191009',
'DS101335',
'DS181045',
]

for number in numbers:
    payload = f'strPartNo_PAItemInq={number}&strFuncType=INVENTORYDATA&strPADealerCode_PAItemInq=AC2011063676&STR_' \
              f'FORM_ID=00602&STR_FUNCTION_ID=IQ&STR_PREMIS=KGL&STR_INSTANT=DLR&STR_APP_ID=00011'

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        data = json.loads(response.text)['DATA']

        if 'dblSellingPrice' in data:
            print(data['dblSellingPrice'])
        else:
            print(f'{number} - Not Found.')
    else:
        print(f'{number} - Not Found.')
