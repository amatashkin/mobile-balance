#!/usr/bin/env python
# coding: utf-8

import requests
import re

from .exceptions import BadResponse
from .utils import check_status_code


def get_balance(number, password):
    session = requests.Session()

    response = session.get('https://login.mts.ru/amserver/UI/Login')
    check_status_code(response, 401)

    csrf_token = re.search(b'name="csrf.sign" value="(.*?)"', response.content)
    csrf_ts_token = re.search(b'name="csrf.ts" value="(.*?)"', response.content) #Второй токен

    if csrf_token is None:
        raise BadResponse('CSRF token not found', response)

    csrf_token = csrf_token.group(1)
    csrf_ts_token = csrf_ts_token.group(1) #Второй токен

    response = session.post('https://login.mts.ru/amserver/UI/Login?service=lk&goto=https://lk.ssl.mts.ru/',
                      data={'IDToken1': number,
                            'IDToken2': password,
                            'csrf.sign': csrf_token,
                            'csrf.ts': csrf_ts_token, #Второй токен
                        },
                      headers={
                          'Accept-Language': 'ru,en;q=0.8',
                      })
    check_status_code(response, 200)

    response = session.get('https://oauth.mts.ru/webapi-1.4/customers/@me')

    check_status_code(response, 200)

    data = response.json()
    relations = data['genericRelations']
    targets = [rel['target'] for rel in relations]
    accounts = [target for target in targets if target['@c'] == '.Account']

    if not accounts:
        raise RuntimeError('Account not found in the data response')

    balance = accounts[0].get('balance')

    if balance is None:
        raise BadResponse('Unable to get balance from JSON', response)

    return float(balance)
