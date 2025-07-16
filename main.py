import asyncio
import qrcode
from dotenv import load_dotenv
import os
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.input_file import BufferedInputFile
from db import add_user, set_full_name, set_phone, init_db, if_registered

load_dotenv()
token = os.getenv("BOT_TOKEN")
print(token)
bot = Bot(token=token)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    user = message.from_user

    if not await if_registered(user.id):
        await add_user(user.id, user.username)
        await message.answer("Введите ФИО")
    

@dp.message(F.text.regexp(r"^[А-Яа-яA-Za-zЁё\s\-]+$"))
async def get_full_name(message: Message):
    await set_full_name(message.from_user.id, message.text.strip())

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Отправьте номер телефона:", reply_markup=kb)

@dp.message(F.contact)
async def get_phone(message: Message):
    await set_phone(message.from_user.id, message.contact.phone_number)
    await message.answer("Вы успешно зарегистрированы!", reply_markup=types.ReplyKeyboardRemove())

    builder = InlineKeyboardBuilder()
    builder.button(text="Получить мой QR-код", callback_data="get_qr")
    await message.answer("Нажмите кнопку ниже, чтобы получить QR-код:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "get_qr")
async def generate_qr(call: CallbackQuery):
    user = call.from_user
    if not await if_registered(user.id):
        await call.answer("Сначала завершите регистрацию", show_alert=True)
        return
    
    qr_data = f"user_id:{user.id}\nusername:{user.username or None}"
    qr_img = qrcode.make(qr_data)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    file = BufferedInputFile(buf.read(), filename="user_qr.png")
    await call.message.answer_photo(photo=file, caption="Твой уникальный QR-код")
    await call.answer()

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("Остановка бота")

if __name__ == "__main__":
    asyncio.run(main())