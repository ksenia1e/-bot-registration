from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

builder_admin = InlineKeyboardBuilder()
builder_admin.row(
    InlineKeyboardButton(text="Разослать сообщение", callback_data="broadcast"),
    InlineKeyboardButton(text="Количество зарегистрированных", callback_data="count_users"),
    InlineKeyboardButton(text="Добавить организатора", callback_data="add_org"),
    InlineKeyboardButton(text="Удалить организатора", callback_data="delete_org"),
    InlineKeyboardButton(text="Провести розыгрыш", callback_data="hold_draw"),
    InlineKeyboardButton(text="Синхронизировать базу данных и гугл таблицы", callback_data="synchronization")
)
builder_admin.adjust(1)
keyboard_admin = builder_admin.as_markup()


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
    InlineKeyboardButton(text="Получить расписание", callback_data="get_schedule"),
    InlineKeyboardButton(text="Мой QR-код", callback_data="get_qr"),
    InlineKeyboardButton(text="Написать в техподдержку", callback_data="technical_support"),
    InlineKeyboardButton(text="Задать вопрос спикеру", callback_data="ask_speaker"),
    InlineKeyboardButton(text="Нетворкинг чат", callback_data="networking_chat")
)
builder_user.adjust(1)
keyboard_user = builder_user.as_markup()

async def get_kb_show_event(position: int, max_position: int):
    builder = InlineKeyboardBuilder()
    if position > 0:
        builder.button(
            text="Назад",
            callback_data=f"prev_event_{position}"
        )
    if position < max_position:
        builder.button(
            text="Далее",
            callback_data=f"next_event_{position}"
        )
    builder.button(
        text="Записаться",
        callback_data=f"sign_up_{position}"
    )
    return builder.as_markup()

async def get_kb_show_my_event(position:int, max_position: int, event_id: int):
    builder = InlineKeyboardBuilder()
    if position > 0:
        builder.button(
            text="Назад",
            callback_data=f"my_prev_event_{position}"
        )
    if position < max_position:
        builder.button(
            text="Далее",
            callback_data=f"my_next_event_{position}"
        )
    builder.button(
        text="Получить QR-код",
        callback_data=f"get_qr_{event_id}"
    )
    return builder.as_markup()


broadcast_builder_yes_no = InlineKeyboardBuilder()
broadcast_builder_yes_no.button(text="Да", callback_data="image_necessary")
broadcast_builder_yes_no.button(text="Нет", callback_data="image_not_necessary")
broadcast_yes_no_kb = broadcast_builder_yes_no.as_markup()

broadcast_builder_send_cancel = InlineKeyboardBuilder()
broadcast_builder_send_cancel.button(text="Отправить", callback_data="send_broadcast")
broadcast_builder_send_cancel_kb = broadcast_builder_send_cancel.as_markup()

async def get_kb_show_speakers(speakers):
    builder = InlineKeyboardBuilder()

    for id, full_name in speakers:
        builder.button(
            text=full_name,
            callback_data=f"speak:{id}:{full_name}"
        )
    builder.adjust(1)
    return builder.as_markup()

networking_builder_link_note = InlineKeyboardBuilder()
networking_builder_link_note.button(text="Получить ссылку", callback_data="get_link")
networking_builder_link_note.button(text="Создать карточку", callback_data="create_note")
networking_builder_link_note_kb = networking_builder_link_note.as_markup()

networking_builder_field = InlineKeyboardBuilder()
networking_builder_field.row(
    InlineKeyboardButton(text="IT", callback_data="field:IT"),
    InlineKeyboardButton(text="Медицина", callback_data="field:Медицина"),
    InlineKeyboardButton(text="Финансы", callback_data="field:Финансы"),
    InlineKeyboardButton(text="Строительство", callback_data="field:Строительство")
).adjust(2)
networking_field_kb = networking_builder_field.as_markup()

networking_builder_yes_no = InlineKeyboardBuilder()
networking_builder_yes_no.button(text="Да", callback_data="image_necessary_net")
networking_builder_yes_no.button(text="Нет", callback_data="image_not_necessary_net")
networking_yes_no_kb = networking_builder_yes_no.as_markup()

networking_builder_send_cancel = InlineKeyboardBuilder()
networking_builder_send_cancel.button(text="Отправить", callback_data="send_note")
networking_send_cancel_kb = networking_builder_send_cancel.as_markup()