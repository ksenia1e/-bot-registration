from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils import Registration
from database import if_registered, add_user

user_router = Router()

@user_router.message(Registration.waiting_for_full_name)
async def get_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await message.answer("Введите номер телефона")
    await state.set_state(Registration.waiting_for_phone)


@user_router.message(Registration.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    data = await state.get_data()

    await add_user(
        int(data["user_id"]),
        data["user_name"],
        data["full_name"],
        data["phone"]
    )

    await message.answer("Вы успешно зарегистрированы!")
    await state.clear()