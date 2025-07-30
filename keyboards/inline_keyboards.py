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
builder_admin.row(
    InlineKeyboardButton(text="Провести розыгрыш", callback_data="hold_draw")
)
builder_admin.row(
    InlineKeyboardButton(text="Синхронизировать базу данных и гугл таблицы", callback_data="synchronization")
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

async def get_kb_show_organozers(organizers):
    builder = InlineKeyboardBuilder()

    for user_id, full_name in organizers:
        builder.button(
            text=full_name,
            callback_data=f"org:{user_id}"
        )
    builder.adjust(2)
    return builder.as_markup()


builder_user = InlineKeyboardBuilder()
builder_user.row(
    InlineKeyboardButton(text="Получить расписание", callback_data="get_schedule")
)
builder_user.row(
    InlineKeyboardButton(text="Получить информацию о розыгрыше", callback_data="get_raffle")
)
keyboard_user = builder_user.as_markup()