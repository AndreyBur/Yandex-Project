from config import *
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
    b = requests.get('https://edge.qiwi.com/funding-sources/v2/persons/' + number[1:] + '/accounts')
    return b.json()


def qiwi_payments(number, token):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    params = {'rows': '50'}
    response = requests.get(f'https://edge.qiwi.com/payment-history/v2/persons/{number}/payments', headers=headers, params=params)
    print(response.json())
    return response.json()['data']


def qiwi_handler(number, token):
    while True:
        txs = qiwi_payments(number, token)
        cur.execute(f'SELECT txn_id FROM Qiwi WHERE number = "{number}"')
        txn_id = cur.fetchone()[0]
        txs = sorted([tx for tx in txs if tx['txnId'] > txn_id], key=lambda tx: tx['txnId'])
        for tx in txs:
            if tx['total']['currency'] == 643 and tx['comment'].isdigit():
                cur.execute(f'SELECT * FROM Users WHERE id = {tx["comment"]}')
                if cur.fetchone():
                    total = int(tx['total']['amount'] * 100)
                    comment = int(tx['comment'])
                    # DEPOSIT SUCCESS
                    cur.execute(f'UPDATE Users SET balance = balance + {total} WHERE id = {comment}')
                    parse = f'{total / 100:.2f}'.replace('.', '\\.')
                    requests.get(f'https://api.telegram.org/bot{API_TOKEN}/sendMessage?chat_id={comment}&text=⚠️ Баланс пополнен на *{parse}* ₽&parse_mode=MarkdownV2')
            cur.execute(f'UPDATE Qiwi SET txn_id = {tx["txnId"]} WHERE number = "{number}"')
            con.commit()
        time.sleep(0.5)


def qiwi_send(number, amount):
    cur.execute(f'SELECT token FROM Qiwi WHERE 1')
    for token in cur.fetchall():


    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    json = {
        'id': str(int(time.time() * 1000)),
        'sum': {'amount': str(amount // 100) + '.' + str(amount % 100), 'currency': 643},
        'paymentMethod': {'type': 'Account', 'accountId': 643},
        'comment': 't.me/hugopay_bot',
        'fields': {'account': number}
    }
    response = requests.post('https://edge.qiwi.com/sinap/api/v2/terms/99/payments', headers=headers, json=json)
    print(response.json())
    return response.json()['data']


if __name__ == '__main__':
    cur.execute('SELECT number, token FROM Qiwi WHERE 1')
    for number, token in cur.fetchall():
        print(number, token)
        qiwi_handler(number, token)
