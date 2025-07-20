from aiogram.types import InlineKeyboardButton
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
keyboard_admin = builder_admin.as_markup()


builder_qr = InlineKeyboardBuilder()
builder_qr.button(text="Получить мой QR-код", callback_data="get_qr")
keyboard_qr = builder_qr.as_markup()