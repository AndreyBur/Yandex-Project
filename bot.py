from aiogram import Bot, Dispatcher, executor, types
from config import *
from payments import qiwi_handler
from threading import Thread
import sqlite3
import logging


API_TOKEN = '5162178464:AAHcPMoses63gVBWbhLiirO4tqCvPQoe4EA'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

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

users = {}


@dp.message_handler(commands=['start', 'help'])
async def command_handler(message: types.Message):
    await message.answer(WELCOME, parse_mode='MarkdownV2', reply_markup=MAIN_KB)


@dp.message_handler()
async def message_handler(message: types.Message):
    tx, id = message.text, message.from_user.id

    cur.execute(f'SELECT * FROM Users WHERE id = {id}')
    user = cur.fetchone()

    if not user:
        cur.execute(f'''INSERT INTO Users VALUES ({id}, 0)''')
        user = (id, 0,)

    if id not in users:
        users[id] = ''

    if tx == 'Перевод 💸':
        await message.answer('В разработке... 🛠')

    elif tx == 'Профиль 👤':
        await message.answer(f'*👤 Ваш профиль*\n\nID: `{id}`\nБаланс: `{user[1] / 100:.2f}` ₽', parse_mode='MarkdownV2')

    elif tx == 'Депозит 💰':
        await message.reply('💰 Выберите метод пополнения', reply_markup=PAYMENT_METHODS_KB)

    elif tx == 'Ваучеры 🎁':
        await message.answer('В разработке... 🛠')

    elif tx == 'Вывод 💳':
        await message.answer('В разработке... 🛠')

    elif tx == 'Поддержка ❓':
        await message.answer('Поддержка: @hugopay_support\nКанал: @hugopay_news')

    elif tx == 'Настройки ⚙️':
        await message.answer('В разработке... 🛠')

    elif users[id]:
        pass

    elif id == 603660417:
        data = tx.split()

        if tx == '/users':
            cur.execute('SELECT COUNT(*) from Users')
            await message.answer(f'Юзеров: {cur.fetchone()[0]}')

        elif tx.startswith('/add_wallet'):
            number, token = data[1:3]
            print(number, token)
            cur.execute(f'INSERT INTO Qiwi VALUES ("{number}", "{token}", 0)')
            Thread(target=qiwi_handler, args=(number, token,)).start()
            await message.answer('done')

    else:
        await message.answer('Не понял вашего сообщения :(\nИспользуйте меню!', reply_markup=MAIN_KB)


@dp.callback_query_handler()
async def query_handler(query: types.CallbackQuery):
    dt, id, mid = query.data, query.from_user.id, query.message.message_id

    if dt == 'cancel':
        users[id] = ''
        await bot.delete_message(id, query.message.reply_to_message.message_id)
        await bot.delete_message(id, mid)

    elif dt == 'deposit_qiwi':
        cur.execute('SELECT number FROM Qiwi ORDER BY RANDOM() LIMIT 1')
        number = cur.fetchone()[0]
        kb = InlineKeyboardMarkup().row(InlineKeyboardButton('Ссылка для депозита', url=QIWI_PAYMENT.format(number, id))).row(CANCEL)
        await bot.edit_message_text(f'Совершите депозит, нажав на кнопку с ссылкой под этим сообщением\\.\nВы также можете сделать перевод вручную по данным ниже:\nНомер: `\\+{number}`\nКомментарий: `{id}`', id, mid, reply_markup=kb, parse_mode='MarkdownV2')

    await bot.answer_callback_query(query.id)


if __name__ == '__main__':
    cur.execute('SELECT number, token FROM Qiwi WHERE 1')
    for number, token in cur.fetchall():
        # print(number, token)
        Thread(target=qiwi_handler, args=(number, token,)).start()

    executor.start_polling(dp, skip_updates=True)
