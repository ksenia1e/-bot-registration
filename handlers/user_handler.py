from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
import logging

from keyboards.inline_keyboards import phone_kb
from utils import Registration
from database import add_user

user_router = Router()
logger = logging.getLogger(__name__)

@user_router.message(Registration.waiting_for_full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())

    logger.info(f"Пользователь {message.from_user.id} ввёл ФИО: {message.text.strip()}")
    
    await message.answer("Отправьте номер телефона, нажав на кнопку ниже:", reply_markup=phone_kb)
    await state.set_state(Registration.waiting_for_phone)


@user_router.message(Registration.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    if message.contact is not None:
        phone = message.contact.phone_number
        logger.info(f"Пользователь {message.from_user.id} отправил номер через кнопку: {phone}")
    else:
        phone = message.text.strip()
        logger.info(f"Пользователь {message.from_user.id} ввёл номер вручную: {phone}")

    await state.update_data(phone=phone)
    data = await state.get_data()

    flag = await add_user(
        int(data["user_id"]),
        data["user_name"],
        data["full_name"],
        data["phone"]
    )
    if flag[0] == True:
        logger.info(f"Пользователь {message.from_user.id} зарегистрирован с данными: {data}")
        await message.answer("Вы успешно зарегистрированы!", reply_markup=ReplyKeyboardRemove())
    else:
        logger.warning(f"Пользователь {message.from_user.id} уже существует. Ошибка: {flag[1]}")
        await message.answer("Вы уже зарегистрированы", reply_markup=ReplyKeyboardRemove())
    await state.clear()