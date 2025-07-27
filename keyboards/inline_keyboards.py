from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

builder_admin = InlineKeyboardBuilder()
builder_admin.row(
    InlineKeyboardButton(text="Разослать сообщение", callback_data="broadcast")
)
builder_admin.row(
    InlineKeyboardButton(text="Кол-во зарегистрированных", callback_data="count_users")
)
builder_admin.row(
    InlineKeyboardButton(text="Добавить организатора", callback_data="add_org")
)
builder_admin.row(
    InlineKeyboardButton(text="Удалить организатора", callback_data="delete_org")
)
keyboard_admin = builder_admin.as_markup()


builder_qr = InlineKeyboardBuilder()
builder_qr.button(text="Получить мой QR-код", callback_data="get_qr")
keyboard_qr = builder_qr.as_markup()

phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отправить номер телефона", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

builder_show_organizers = InlineKeyboardBuilder()