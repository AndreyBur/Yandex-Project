from aiogram.types import *


API_TOKEN = '5162178464:AAHcPMoses63gVBWbhLiirO4tqCvPQoe4EA'

QIWI_PAYMENT = 'https://qiwi.com/payment/form/99?extra%5B%27account%27%5D={}&extra%5B%27comment%27%5D={}&currency=643&blocked[0]=account&blocked[1]=comment'

WELCOME = '''*👋 Добро пожаловать*

*💸 HugoPay* — Удобный инструмент для принятия платежей, а также для внутренних переводов между пользователями\\.
Все действия выполняются через меню этого бота\\.

Бот запустился совсем недавно и могут быть недоработки\\.
Если вы найдете любые баги или опечатки, напишите пожалуйста нашей поддержке: @hugopay\\_support'''

CANCEL = InlineKeyboardButton('Отмена 🗑', callback_data='cancel')

MAIN_KB = ReplyKeyboardMarkup(resize_keyboard=True)
MAIN_KB.row(KeyboardButton('Перевод 💸'), KeyboardButton('Профиль 👤'))
MAIN_KB.row(KeyboardButton('Депозит 💰'), KeyboardButton('Ваучеры 🎁'), KeyboardButton('Вывод 💳'))
MAIN_KB.row(KeyboardButton('Поддержка ❓'), KeyboardButton('Настройки ⚙️'))

CANCEL_KB = InlineKeyboardMarkup().add(CANCEL)

PAYMENT_METHODS_KB = InlineKeyboardMarkup()
PAYMENT_METHODS_KB.row(
    InlineKeyboardButton('Qiwi 🥝', callback_data='deposit_qiwi'),
    # InlineKeyboardButton('BNB (BEP20) 🟢', callback_data='deposit_bnbbep20')
)
PAYMENT_METHODS_KB.row(CANCEL)
