import qrcode
from io import BytesIO
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_file import BufferedInputFile

from utils import AddOrganizer
from bot import bot, bot_username
from keyboards.inline_keyboards import keyboard_admin, keyboard_qr
from database import get_user_role, get_users, add_organizer_, get_number_of_users_

admin_router = Router()

@admin_router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if await get_user_role(message.from_user.id) != "admin":
        await message.answer("Нет прав доступа")
        return
    
    await message.answer("Выберете опцию: ",reply_markup=keyboard_admin)

@admin_router.callback_query(F.data == "add_org")
async def add_organizer(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ID")
    await state.set_state(AddOrganizer.waiting_for_user_id)

@admin_router.message(AddOrganizer.waiting_for_user_id)
async def add_user_id(message: Message, state: FSMContext):
    await state.update_data(user_id=message.text.strip())
    await message.answer("Введите username")
    await state.set_state(AddOrganizer.waiting_for_user_name)

@admin_router.message(AddOrganizer.waiting_for_user_name)
async def add_user_name(message: Message, state: FSMContext):
    await state.update_data(user_name=message.text.strip())
    await message.answer("Введите ФИО")
    await state.set_state(AddOrganizer.waiting_for_full_name)

@admin_router.message(AddOrganizer.waiting_for_full_name)
async def add_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await message.answer("Введите номер телефона")
    await state.set_state(AddOrganizer.waiting_for_phone)

@admin_router.message(AddOrganizer.waiting_for_phone)
async def add_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    data = await state.get_data()

    try:
        await add_organizer_(
            int(data["user_id"]),
            data["user_name"],
            data["full_name"],
            data["phone"]
        )
        await message.answer("Организатор успешно добавлен")
    except Exception as e:
        await message.answer(f"Ошибка в добавлении: {e}")

    await state.clear()

@admin_router.callback_query(F.data == "broadcast")
async def send_newsletter(callback: CallbackQuery):
    text = "Всех приветствую, для быстрой регистрации на мероприятии покажите QR-код, который можно получить по кнопке ниже"
    
    users = await get_users()
    for row in users:
        try:
            await bot.send_message(chat_id=row[0], text=text, reply_markup=keyboard_qr)
        except Exception as e:
            print(f"Ошибка при отправке пользователю {row[0]}: {e}")

    await callback.answer("Рассылка завершена.")

@admin_router.callback_query(F.data == "get_qr")
async def generate_qr(call: CallbackQuery):
    user = call.from_user

    qr_data = f"https://t.me/{bot_username}?start={user.id}"
    qr_img = qrcode.make(qr_data)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    file = BufferedInputFile(buf.read(), filename="user_qr.png")
    await call.message.answer_photo(photo=file, caption="Твой уникальный QR-код")
    await call.answer()

@admin_router.callback_query(F.data == "count_users")
async def get_number_of_users(message: Message):
    num = await get_number_of_users_()
    await message.answer(f"Количество зарегистрированных: {num}")