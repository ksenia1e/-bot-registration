from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils import Registration
from database import if_registered, get_user_role, set_checked_in, get_checked_in

start_router = Router()

@start_router.message(F.text.startswith("/start"))
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
            await message.answer("Добро пожаловать! Вы уже зарегистрированы на мероприятие!")
    else:
        await state.update_data(user_id=user.id, user_name=user.username)
        await message.answer("Добро пожаловать! Введите ФИО")
        await state.set_state(Registration.waiting_for_full_name)