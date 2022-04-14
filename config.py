from aiogram.types import *


QIWI_PAYMENT = 'https://qiwi.com/payment/form/99?extra%5B%27account%27%5D={}&extra%5B%27comment%27%5D={}&currency=643&blocked[0]=account&blocked[1]=comment'

WELCOME = '''*👋 Добро пожаловать*

*💸 HugoPay* — Удобный инструмент для принятия платежей, а также для внутренних переводов между пользователями\\.
Все действия выполняются через меню этого бота\\.

Бот запустился совсем недавно и могут быть недоработки\\.
Если вы найдете любые баги или опечатки, напишите пожалуйста нашей поддержке: @hugopay\\_support'''

CANCEL = InlineKeyboardButton('Отмена 🗑', callback_data='cancel')
CONFIRM = InlineKeyboardButton('Подтвердить ✅', callback_data='confirm')
CANCEL_2 = InlineKeyboardButton('Отменить ❌', callback_data='cancel')

MAIN_KB = ReplyKeyboardMarkup(resize_keyboard=True)
MAIN_KB.row(KeyboardButton('Перевод 💸'), KeyboardButton('Профиль 👤'))
MAIN_KB.row(KeyboardButton('Депозит 💰'), KeyboardButton('Ваучеры 🎁'), KeyboardButton('Вывод 💳'))
MAIN_KB.row(KeyboardButton('Поддержка ❓'), KeyboardButton('Настройки ⚙️'))

CANCEL_KB = InlineKeyboardMarkup().add(CANCEL)

CONFIRM_KB = InlineKeyboardMarkup().row(CONFIRM, CANCEL_2)

DEPOSIT_METHODS_KB = InlineKeyboardMarkup()
DEPOSIT_METHODS_KB.row(
    InlineKeyboardButton('Qiwi 🥝', callback_data='deposit_qiwi'),
    # InlineKeyboardButton('BNB (BEP20) 🟢', callback_data='deposit_bnbbep20')
)
DEPOSIT_METHODS_KB.row(CANCEL)

WITHDRAW_METHODS_KB = InlineKeyboardMarkup()
WITHDRAW_METHODS_KB.row(
    InlineKeyboardButton('Qiwi 2% 🥝', callback_data='withdraw_qiwi'),
    # InlineKeyboardButton('BNB (BEP20) 🟢', callback_data='deposit_bnbbep20')
)
WITHDRAW_METHODS_KB.row(CANCEL)
