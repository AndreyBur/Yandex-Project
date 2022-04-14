from config import *
from secret import *
import requests
import time
import sqlite3


con = sqlite3.connect('db.sqlite', check_same_thread=False)
cur = con.cursor()


def qiwi_balance(number, token):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    b = requests.get(f'https://edge.qiwi.com/funding-sources/v2/persons/{number}/accounts', headers=headers)
    return int(b.json()['accounts'][0]['balance']['amount'] * 100)


def qiwi_payments(number, token):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    params = {'rows': '50'}
    response = requests.get(f'https://edge.qiwi.com/payment-history/v2/persons/{number}/payments', headers=headers, params=params)
    return response.json()['data']


def qiwi_handler(number, token, lock):
    while True:
        txs = qiwi_payments(number, token)
        with lock:
            cur.execute(f'SELECT txn_id FROM Qiwi WHERE number = "{number}"')
            txn_id = cur.fetchone()[0]
        txs = sorted([tx for tx in txs if tx['txnId'] > txn_id], key=lambda tx: tx['txnId'])
        for tx in txs:
            if tx['total']['currency'] == 643 and tx['comment'].isdigit():
                with lock:
                    cur.execute(f'SELECT * FROM Users WHERE id = {tx["comment"]}')
                    res = cur.fetchone()
                if res:
                    total = int(tx['total']['amount'] * 100)
                    comment = int(tx['comment'])
                    # DEPOSIT SUCCESS
                    with lock:
                        cur.execute(f'UPDATE Users SET balance = balance + {total} WHERE id = {comment}')
                        con.commit()
                    parse = f'{total / 100:.2f}'.replace('.', '\\.')
                    requests.get(f'https://api.telegram.org/bot{API_TOKEN}/sendMessage?chat_id={comment}&text=⚠️ Баланс пополнен на *{parse}* ₽&parse_mode=MarkdownV2')
            with lock:
                cur.execute(f'UPDATE Qiwi SET txn_id = {tx["txnId"]} WHERE number = "{number}"')
                con.commit()
        time.sleep(3)


def qiwi_send(number, amount, lock):
    cur.execute(f'SELECT number, token FROM Qiwi WHERE 1')
    res = cur.fetchall()

    for number_, token in res:
        if qiwi_balance(number_, token) >= amount:
            try:
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
                json = {
                    'id': str(int(time.time() * 1000)),
                    'sum': {'amount': str(int(int(amount) / 1.02) / 100), 'currency': '643'},
                    'paymentMethod': {'type': 'Account', 'accountId': '643'},
                    'comment': '',
                    'fields': {'account': number}
                }
                response = requests.post('https://edge.qiwi.com/sinap/api/v2/terms/99/payments', headers=headers, json=json)
                print(response.text)
                return response.json()['transaction']['state']['code'] == 'Accepted'
            except:
                return False

    return False


if __name__ == '__main__':
    cur.execute('SELECT number, token FROM Qiwi WHERE 1')

    qiwi_send('+79518439831', 101)

    exit()

    for number, token in cur.fetchall():
        qiwi_handler(number, token)
