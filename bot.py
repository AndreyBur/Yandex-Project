from aiogram import Bot, Dispatcher, executor, types
from config import *
from secret import *
from payments import qiwi_handler, qiwi_send, qiwi_balance
from threading import Thread, Lock
import sqlite3
import logging
import re
import json
import random


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

lock = Lock()

con = sqlite3.connect('db.sqlite', check_same_thread=False)
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY,
    balance INTEGER
)''')
cur.execute('''CREATE TABLE IF NOT EXISTS Qiwi (
    number TEXT PRIMARY KEY,
    token TEXT,
    txn_id INTEGER
)''')
cur.execute('''CREATE TABLE IF NOT EXISTS Vouchers (
    id INTEGER PRIMARY KEY,
    amount INTEGER,
    activations INTEGER,
    users TEXT,
    creator INTEGER
)''')

number_re = re.compile(r'[\d|+]\d{6,12}')
amount_re = re.compile(r'\d+(.\d{1,2}){0,1}')

users = {}


@dp.message_handler(commands=['start', 'help'])
async def command_handler(message: types.Message):
    tx, id = message.text, message.from_user.id

    with lock:
        cur.execute(f'SELECT * FROM Users WHERE id = {id}')
        if not cur.fetchone():
            cur.execute(f'''INSERT INTO Users VALUES ({id}, 0)''')
            con.commit()

    if tx.startswith('/start '):
        a, v = tx[7], tx[9:]
        print([a, v])
        if a == 'v':
            # Voucher
            with lock:
                cur.execute(f'SELECT * FROM Vouchers WHERE id = {v}')
                voucher = cur.fetchone()
                if voucher:
                    u = json.loads(voucher[3])
                    if id not in u:
                        u.append(id)
                        if voucher[2] == 1:
                            cur.execute(f'DELETE FROM Vouchers WHERE id = {v}')
                        else:
                            cur.execute(f'UPDATE Vouchers SET activations = activations - 1, users = "{json.dumps(u)}" WHERE id = {v}')
                        cur.execute(f'UPDATE Users SET balance = balance + {voucher[1]} WHERE id = {id}')
                        con.commit()
                        await message.answer(f'🎁 Ваучер активирован\\!\nВы получили: `{voucher[1] / 100:.2f}` ₽', parse_mode='MarkdownV2', reply_markup=MAIN_KB)
                        await bot.send_message(voucher[4], f'🎁 `{id}` активировал ваш ваучер на `{voucher[1] / 100:.2f}` ₽', parse_mode='MarkdownV2')
                    else:
                        await message.answer('Вы уже активировали этот ваучер!', reply_markup=MAIN_KB)
                else:
                    await message.answer('Ваучер не найден! Возможно, его уже активировали максимальное количество раз.', reply_markup=MAIN_KB)
    else:
        await message.answer(WELCOME, parse_mode='MarkdownV2', reply_markup=MAIN_KB)


@dp.message_handler()
async def message_handler(message: types.Message):
    tx, id = message.text, message.from_user.id

    with lock:
        cur.execute(f'SELECT * FROM Users WHERE id = {id}')
        user = cur.fetchone()

    if not user:
        with lock:
            cur.execute(f'''INSERT INTO Users VALUES ({id}, 0)''')
            con.commit()
        user = (id, 0,)

    if id not in users:
        users[id] = ''

    if tx == 'Перевод 💸':
        await message.answer('Отправьте ID пользователя для перевода')
        users[id] = 'send_id'

    elif tx == 'Профиль 👤':
        await message.answer(f'*👤 Ваш профиль*\n\nID: `{id}`\nБаланс: `{user[1] / 100:.2f}` ₽', parse_mode='MarkdownV2')

    elif tx == 'Депозит 💰':
        await message.reply('💰 Выберите метод пополнения', reply_markup=DEPOSIT_METHODS_KB)

    elif tx == 'Ваучеры 🎁':
        await message.answer('Отправьте сумму одной активации ваучера \\(мин\\. `1.00` ₽\\)', parse_mode='MarkdownV2')
        users[id] = 'voucher_amount'

    elif tx == 'Вывод 💳':
        await message.reply('💳 Выберите метод вывода', reply_markup=WITHDRAW_METHODS_KB)

    elif tx == 'Поддержка ❓':
        await message.answer('Поддержка: @hugopay_support\nКанал: @hugopay_news')

    elif tx == 'Настройки ⚙️':
        await message.answer('В разработке... 🛠')

    elif users[id] == 'withdraw_qiwi_number':
        if number_re.fullmatch(tx):
            if tx[0] == '+':
                number = tx
            else:
                number = '+' + tx
            users[id] = 'withdraw_qiwi_amount_' + number
            await message.answer('Введите сумму для вывода')
        else:
            await message.answer('Некорректный номер! Попробуйте ещё раз.')

    elif users[id].startswith('withdraw_qiwi_amount_'):
        if amount_re.fullmatch(tx):
            if '.' in tx:
                amount = int(tx.split('.')[0]) * 100
                if len(tx.split('.')[1]) == 1:
                    amount += int(tx.split('.')[1]) * 10
                else:
                    amount += int(tx.split('.')[1])
            else:
                amount = int(tx) * 100

            if amount >= 100:
                with lock:
                    cur.execute(f'SELECT balance FROM Users WHERE id = {id}')
                    res = cur.fetchone()[0]
                if res >= amount:
                    number = users[id].split('_')[-1]
                    await message.answer(f'Вы подтверждаете операцию превода `{amount / 100:.2f}` ₽ на номер *{number}*'.replace('+', '\\+'), parse_mode='MarkdownV2', reply_markup=CONFIRM_KB)
                    users[id] = f'withdraw_qiwi_confirm_{number}_{amount}'
                else:
                    await message.answer('У вас недостаточно средств для совершения операции! Попробуйте ещё раз.')
            else:
                await message.answer('Минимальная сумма для вывода на Qiwi — `1.00` ₽', parse_mode='MarkdownV2')
        else:
            await message.answer('Некорректная сумма! Попробуйте ещё раз.')

    elif users[id] == 'send_id':
        if set(tx) <= set('0123456789') and 5 < len(tx) < 15:
            with lock:
                cur.execute(f'SELECT * FROM Users WHERE id = {tx}')
                res = cur.fetchall()
            if res:
                await message.answer(f'Отправьте сумму перевода \\(макс\\. `{user[1] / 100:.2f}` ₽\\)', parse_mode='MarkdownV2')
                users[id] = 'send_amount_' + tx
            else:
                await message.answer('Пользователь с таким ID не найден! Попробуйте еще раз.')
        else:
            await message.answer('Некорректный ID! Попробуйте еще раз.')

    elif users[id].startswith('send_amount_'):
        if amount_re.fullmatch(tx):
            if '.' in tx:
                amount = int(tx.split('.')[0]) * 100
                if len(tx.split('.')[1]) == 1:
                    amount += int(tx.split('.')[1]) * 10
                else:
                    amount += int(tx.split('.')[1])
            else:
                amount = int(tx) * 100

            if amount > 0:
                with lock:
                    cur.execute(f'SELECT balance FROM Users WHERE id = {id}')
                    res = cur.fetchone()[0]
                if res >= amount:
                    uid = users[id].split('_')[-1]
                    await message.answer(f'Вы подтверждаете операцию превода `{amount / 100:.2f}` ₽ пользователю *{uid}*', parse_mode='MarkdownV2', reply_markup=CONFIRM_KB)
                    users[id] = f'send_confirm_{uid}_{amount}'
                else:
                    await message.answer('У вас недостаточно средств для совершения операции! Попробуйте ещё раз.')
            else:
                await message.answer('Минимальная сумма для перевода — `0.01` ₽', parse_mode='MarkdownV2')
        else:
            await message.answer('Некорректная сумма! Попробуйте ещё раз.')

    elif users[id] == 'voucher_amount':
        if amount_re.fullmatch(tx):
            if '.' in tx:
                amount = int(tx.split('.')[0]) * 100
                if len(tx.split('.')[1]) == 1:
                    amount += int(tx.split('.')[1]) * 10
                else:
                    amount += int(tx.split('.')[1])
            else:
                amount = int(tx) * 100

            if amount >= 100:
                with lock:
                    cur.execute(f'SELECT balance FROM Users WHERE id = {id}')
                    res = cur.fetchone()[0]
                if res >= amount:
                    await message.answer(f'Отправьте количество активаций ваучера \\(макс\\. `{res // amount}`\\)', parse_mode='MarkdownV2')
                    users[id] = f'voucher_number_{amount}'
                else:
                    await message.answer('У вас недостаточно средств для совершения операции! Попробуйте ещё раз.')
            else:
                await message.answer('Минимальная сумма ваучера — `1.00` ₽', parse_mode='MarkdownV2')
        else:
            await message.answer('Некорректная сумма! Попробуйте ещё раз.')

    elif users[id].startswith('voucher_number'):
        if set(tx) <= set('0123456789') and int(tx) > 0:
            amount, number = int(users[id].split('_')[-1]), int(tx)
            with lock:
                cur.execute(f'SELECT balance FROM Users WHERE id = {id}')
                res = cur.fetchone()[0]
            if res >= amount * number:
                # nice, let's create voucher
                while True:
                    voucher = random.randint(1000000, 9999999)
                    cur.execute(f'SELECT * FROM Vouchers WHERE id = {voucher}')
                    if not cur.fetchall():
                        break
                cur.execute(f'INSERT INTO Vouchers VALUES ({voucher}, {amount}, {number}, "[]", {id})')
                cur.execute(f'UPDATE Users SET balance = balance - {amount * number} WHERE id = {id}')
                con.commit()
                users[id] = ''
                kb = InlineKeyboardMarkup().row(InlineKeyboardButton(text='🎈 Поделиться', switch_inline_query=f't.me/hugopay_bot?start=v_{voucher}'))
                await message.answer(f'Ваучер создан\\!\n`{number}` Активаций по `{amount / 100:.2f}` ₽\n\nt\\.me/hugopay\\_bot?start\\=v\\_{voucher}', parse_mode='MarkdownV2', reply_markup=kb)
            else:
                await message.answer('У вас недостаточно средств для совершения операции! Попробуйте ещё раз.')
        else:
            await message.answer('Некорректная сумма! Попробуйте ещё раз.')

    elif id == 603660417:
        data = tx.split()

        if tx == '/users':
            with lock:
                cur.execute('SELECT COUNT(*) from Users')
                await message.answer(f'Юзеров: {cur.fetchone()[0]}')

        elif tx.startswith('/add_wallet'):
            number, token = data[1:3]
            with lock:
                cur.execute(f'INSERT INTO Qiwi VALUES ("{number}", "{token}", 0)')
                con.commit()
            Thread(target=qiwi_handler, args=(number, token, lock,)).start()
            await message.answer('done')

        elif tx.startswith('/del_wallet'):
            number = data[1]
            with lock:
                cur.execute(f'DELETE FROM Qiwi WHERE number = {number}')
                con.commit()
            await message.answer('done')

        elif tx.startswith('/wallets'):
            with lock:
                cur.execute(f'SELECT number, token FROM Qiwi WHERE 1')
                res = cur.fetchall()
            result = []
            for number, token in res:
                result.append((number, qiwi_balance(number, token)))
            print(result)
            await message.answer('\n'.join([f'{number}: {balance / 100:.2f}' for number, balance in result]))

    else:
        await message.answer('Не понял вашего сообщения :(\nИспользуйте меню!', reply_markup=MAIN_KB)


@dp.callback_query_handler()
async def query_handler(query: types.CallbackQuery):
    dt, id, mid = query.data, query.from_user.id, query.message.message_id

    if dt == 'cancel':
        users[id] = ''
        try:
            await bot.delete_message(id, query.message.reply_to_message.message_id)
        except:
            pass
        await bot.delete_message(id, mid)

    elif dt == 'deposit_qiwi':
        with lock:
            cur.execute('SELECT number FROM Qiwi ORDER BY RANDOM() LIMIT 1')
            number = cur.fetchone()[0]
        kb = InlineKeyboardMarkup().row(InlineKeyboardButton('Ссылка для депозита', url=QIWI_PAYMENT.format(number, id)))
        await bot.edit_message_text(f'Совершите депозит, нажав на кнопку с ссылкой под этим сообщением\\.\nВы также можете сделать перевод вручную по данным ниже:\nНомер: `\\+{number}`\nКомментарий: `{id}`', id, mid, reply_markup=kb, parse_mode='MarkdownV2')

    elif dt == 'withdraw_qiwi':
        await bot.edit_message_text('Отправте номер Qiwi кошелька в формате "+79991234567"', id, mid)
        users[id] = 'withdraw_qiwi_number'

    elif dt == 'confirm':
        if users[id].startswith('withdraw_qiwi_confirm_'):
            number, amount = users[id].split('_')[-2:]
            amount = int(amount)
            with lock:
                cur.execute(f'SELECT balance FROM Users WHERE id = {id}')
                res = cur.fetchone()[0]
                if res >= amount:
                    if qiwi_send(number, amount, lock):
                        cur.execute(f'UPDATE Users SET balance = balance - {amount} WHERE id = {id}')
                        con.commit()
                        await bot.edit_message_text(f'💸 Вывод `{amount / 100:.2f}` ₽ на кошелек Qiwi *{number}*'.replace('+', '\\+'), id, mid, parse_mode='MarkdownV2')
                    else:
                        await bot.edit_message_text('Произошла ошибка во время перевода! Попробуйте повторить позже.', id, mid)
                else:
                    await message.answer('У вас недостаточно средств для совершения операции! Попробуйте ещё раз.')

        elif users[id].startswith('send_confirm_'):
            uid, amount = map(int, users[id].split('_')[-2:])
            with lock:
                cur.execute(f'SELECT balance FROM Users WHERE id = {id}')
                res = cur.fetchone()[0]
                if res >= amount:
                    cur.execute(f'UPDATE Users SET balance = balance - {amount} WHERE id = {id}')
                    cur.execute(f'UPDATE Users SET balance = balance + {amount} WHERE id = {uid}')
                    con.commit()
                    await bot.edit_message_text(f'💸 Перевод `{amount / 100:.2f}` ₽ пользователю *{uid}*', id, mid, parse_mode='MarkdownV2')
                    await bot.send_message(uid, f'💰 Вы получили перевод `{amount / 100:.2f}` ₽ от пользователя *{id}*', parse_mode='MarkdownV2')
                else:
                    await message.answer('У вас недостаточно средств для совершения операции! Попробуйте ещё раз.')

    await bot.answer_callback_query(query.id)


if __name__ == '__main__':
    cur.execute('SELECT number, token FROM Qiwi WHERE 1')
    for number, token in cur.fetchall():
        Thread(target=qiwi_handler, args=(number, token, lock,)).start()

    executor.start_polling(dp, skip_updates=True)
