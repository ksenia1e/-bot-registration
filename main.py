import asyncio
import qrcode
from dotenv import load_dotenv
import os
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.input_file import BufferedInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from db import add_user, init_db, if_registered, get_user_role, get_users, add_organizer_, get_number_of_users_, get_checked_in, set_checked_in

load_dotenv()
token = os.getenv("BOT_TOKEN")

bot = Bot(token=token)
dp = Dispatcher()

class Registration(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()

class AddOrganizer(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_user_name = State()
    waiting_for_full_name = State()
    waiting_for_phone = State()

@dp.message(F.text.startswith("/start"))
async def start_handler(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    user = message.from_user
    if await if_registered(user.id):
        if len(parts) > 1:
            ref_id = parts[1]
            if await get_user_role(user.id) != "user":
                if await get_checked_in(ref_id) == 0:
                    await set_checked_in(ref_id)
                    await message.answer("Пользователь регистрировался и отмечен как присутствующий")
                elif await get_checked_in(ref_id) == 1:
                    await message.answer("Пользователь уже отмечен как присутствующий")
                else:
                    await message.answer("Пользователь не регистрировался на мероприятии")
            else:
                await message.answer("Нет прав доступа")
    else:
        await state.update_data(user_id=user.id, user_name=user.username)
        await message.answer("Введите ФИО")
        await state.set_state(Registration.waiting_for_full_name)

@dp.message(Registration.waiting_for_full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await message.answer("Введите номер телефона")
    await state.set_state(Registration.waiting_for_phone)

@dp.message(Registration.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    data = await state.get_data()

    await add_user(
        int(data["user_id"]),
        data["user_name"],
        data["full_name"],
        data["phone"]
    )

    await message.answer("Вы успешно зарегистрированы")
    await state.clear()

@dp.message(F.text == "/admin")
async def admin_panel(message: Message):
    if await get_user_role(message.from_user.id) != "admin":
        await message.answer("Нет прав доступа")
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Разослать сообщение", callback_data="broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="Кол-во зарегистрированных", callback_data="count_users")
    )
    keyboard = builder.as_markup()
    await message.answer("Выберете опцию: ",reply_markup=keyboard)
    KeyboardButton(text="Добавить организатора")

@dp.message(F.text == "Добавить организатора")
async def add_organizer(message: Message, state: FSMContext):
    await message.answer("Введите ID")
    await state.set_state(AddOrganizer.waiting_for_user_id)

@dp.message(AddOrganizer.waiting_for_user_id)
async def add_user_id(message: Message, state: FSMContext):
    await state.update_data(user_id=message.text.strip())
    await message.answer("Введите username")
    await state.set_state(AddOrganizer.waiting_for_user_name)

@dp.message(AddOrganizer.waiting_for_user_name)
async def add_user_name(message: Message, state: FSMContext):
    await state.update_data(user_name=message.text.strip())
    await message.answer("Введите ФИО")
    await state.set_state(AddOrganizer.waiting_for_full_name)

@dp.message(AddOrganizer.waiting_for_full_name)
async def add_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await message.answer("Введите номер телефона")
    await state.set_state(AddOrganizer.waiting_for_phone)

@dp.message(AddOrganizer.waiting_for_phone)
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

@dp.callback_query(F.data == "broadcast")
async def send_newsletter(callback: CallbackQuery):
    text = "Всех приветствую, для быстрой регистрации на мероприятии покажите QR-код, который можно получить по кнопке ниже"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Получить мой QR-код", callback_data="get_qr")
    keyboard = builder.as_markup()

    users = await get_users()
    for row in users:
        try:
            await bot.send_message(chat_id=row[0], text=text, reply_markup=keyboard)
        except Exception as e:
            print(f"Ошибка при отправке пользователю {row[0]}: {e}")

    await callback.answer("Рассылка завершена.")

@dp.callback_query(F.data == "get_qr")
async def generate_qr(call: CallbackQuery):
    user = call.from_user
    bot_username = os.getenv("BOT_USERNAME")

    qr_data = f"https://t.me/{bot_username}?start={user.id}"
    qr_img = qrcode.make(qr_data)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    file = BufferedInputFile(buf.read(), filename="user_qr.png")
    await call.message.answer_photo(photo=file, caption="Твой уникальный QR-код")
    await call.answer()

@dp.callback_query(F.data == "count_users")
async def get_number_of_users(message: Message):
    num = await get_number_of_users_()
    await message.answer(f"Количество зарегистрированных: {num}")

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())