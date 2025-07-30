from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import logging

from utils import Registration
from database import if_registered, get_user_role, set_checked_in, get_checked_in
from keyboards.inline_keyboards import keyboard_user

start_router = Router()
logger = logging.getLogger(__name__)

@start_router.message(F.text.startswith("/start"))
async def start_handler(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    user = message.from_user

    logger.info(f"Получена команда /start от пользователя {user.id} (@{user.username})")
    
    if len(parts) > 1:
        if await if_registered(user.id):
            ref_id = parts[1]
            logger.info(f"Попытка отметить присутствие для пользователя с ID {ref_id} админом {user.id}")

            if await get_user_role(user.id) != "user":
                checked = await get_checked_in(ref_id)
                if checked == 0:
                    await set_checked_in(ref_id)
                    await message.answer("Пользователь регистрировался и отмечен как присутствующий")
                    logger.info(f"Пользователь {ref_id} отмечен как присутствующий")
                elif checked == 1:
                    await message.answer("Пользователь уже отмечен как присутствующий")
                    logger.info(f"Пользователь {ref_id} уже был отмечен ранее")
                else:
                    await message.answer("Пользователь не регистрировался на мероприятии")
                    logger.warning(f"Попытка отметить неизвестного пользователя: {ref_id}")
            else:
                await message.answer("Нет прав доступа")
                logger.warning(f"Пользователь {user.id} не имеет прав на отметку других")
        else:
            await message.answer("Добро пожаловать! Вы уже зарегистрированы на мероприятие!")
            logger.info(f"Зарегистрированный пользователь {user.id} вошёл без параметров")
    else:
        if await if_registered(user.id):
            logger.info(f"Вывод меню для пользоватедя {user.id}")
            await message.answer("Меню", reply_markup=keyboard_user)
        else:
            await state.update_data(user_id=user.id, user_name=user.username)
            await message.answer("Добро пожаловать! Введите ФИО")
            await state.set_state(Registration.waiting_for_full_name)
            logger.info(f"Начата регистрация нового пользователя {user.id}")