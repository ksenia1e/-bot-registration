from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from keyboards.inline_keyboards import phone_kb, keyboard_user, get_kb_show_event
from utils import Registration
from database import add_user, get_all_table, add_user_event, add_user_role

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
    if message.contact is None:
        logger.warning(f"Пользователь {message.from_user.id} ввёл номер вручную")
        await message.answer("Пожалуйста, отправьте номер через кнопку ниже", reply_markup=phone_kb)
        await state.set_state(Registration.waiting_for_phone)
        return
    
    phone = message.contact.phone_number
    logger.info(f"Пользователь {message.from_user.id} отправил номер через кнопку: {phone}")

    if not phone:
        await message.answer("Не удалось получить номер")
        logger.warning(f"Не удалось получить номер пользователя {message.from_user.id}")
        return
    
    logger.info(f"Номер получен: {phone}")
    await state.update_data(phone=phone)

    data = await state.get_data()
    try:
        await add_user(
            int(data["user_id"]),
            data["user_name"],
            data["full_name"],
            data["phone"]
        )
        await add_user_role(
            int(data["user_id"]),
            "user"
        )

        logger.info(f"Пользователь {message.from_user.id} зарегистрирован с данными: {data}")
        await message.answer("Вы успешно зарегистрированы!", reply_markup=ReplyKeyboardRemove())
        await message.answer("Меню", reply_markup=keyboard_user)
    except Exception as e:
        logger.error(f"Ошибка в добавление ползователя: {e}")
        await message.answer("Ошибка регистрации. Снова нажмите на команду '/start'")

    await state.clear()

@user_router.callback_query(F.data == "get_schedule")
async def get_schedule(callback: CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запрашивает расписание мероприятий")
    data = await get_all_table("schedule")

    if not data:
        logger.info("Таблица schedule пуста")
        await callback.message.answer("Сейчас не проводится никаких мероприятий")
        await callback.answer()
        return
    
    await callback.answer()
    await show_current_event(callback, data, 0)

async def show_current_event(callback: CallbackQuery, events: list, position: int):
    logger.info(f"Вывод меропртиятия с позицией: {position}")

    row = events[position]
    response = (
        f"🎯 **{row[1]}**\n"
        f"📅 {row[2]}\n"
        f"🕒 {row[3]} - {row[4]}\n"
        f"📍 {row[5]}\n"
        f"📌 {row[6]}\n"
        f"─────────────────── "
        f"Мероприятие {position+1}/{len(events)}"
    )
    keyboard = await get_kb_show_event(position, len(events)-1)
    await callback.message.answer(response, reply_markup=keyboard)
    await callback.answer()

@user_router.callback_query(F.data.startswith("next_event"))
async def get_next_event(callback: CallbackQuery):
    position = int(callback.data.split("_")[-1]) + 1
    logger.info(f"Вывод мероприятия: {position}")

    data = await get_all_table("schedule")
    await callback.answer()
    await show_current_event(callback, data, position)

@user_router.callback_query(F.data.startswith("prev_event"))
async def get_next_event(callback: CallbackQuery):
    position = int(callback.data.split("_")[-1]) - 1
    logger.info(f"Вывод мероприятия: {position}")

    data = await get_all_table("schedule")
    await callback.answer()
    await show_current_event(callback, data, position)

@user_router.callback_query(F.data.startswith("sign_up"))
async def sign_up_event(callback: CallbackQuery):
    user_id = callback.from_user.id
    event_id = int(callback.data.split("_")[-1]) + 1

    result = await add_user_event(user_id, event_id)
    if result[0]:
        logger.info(f"Пользователь {user_id} записался на мероприятие {event_id}")
        await callback.message.answer(f"Вы успешно записались на мероприятие!")
    else:
        logger.warning(f"Ошибка в записи пользователя {user_id} на мероприятие {event_id}: {result[1]}")
        await callback.message.answer("Не удалось записаться на мероприятие")

    await callback.answer()
    
@user_router.callback_query(F.data == "get_raffle")
async def get_raffle(callback: CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запрашивает информацию о розыгрыше")
    data = await get_all_table("raffle")
    response = "\n".join(
        f"🏆 **{row[1]}**\n"
        f"📅 {row[2]}\n"
        f"⏰ {row[3]} – {row[4]}\n"
        f"💰 Призы: {row[5]}\n"
        f"────────────────────"
        for row in data
    )

    await callback.message.answer(response, reply_markup=keyboard_user)
    await callback.answer()