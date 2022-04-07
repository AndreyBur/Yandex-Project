import requests
import time
import sqlite3


con = sqlite3.connect('db.sqlite', check_same_thread=False)
cur = con.cursor()


def get_payments(number, token):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    params = {'rows': '10'}
    response = requests.get(f'https://edge.qiwi.com/payment-history/v2/persons/{number}/payments', headers=headers, params=params)
    return response.json()['data']


def qiwi_handler(number, token):
    while True:
        txs = get_payments(number, token)
        ids = [tx['txnId'] for tx in txs]
        print(max(ids))
        cur.execute(f'SELECT txn_id FROM Qiwi WHERE number = "{number}"')
        print(cur.fetchone())
        time.sleep(5)
