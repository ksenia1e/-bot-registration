from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging
from io import BytesIO
import qrcode
from aiogram.types.input_file import BufferedInputFile

from bot import bot_username, bot, technical_support_chat, speakers_chat
from keyboards.inline_keyboards import phone_kb, keyboard_user, get_kb_show_event, get_kb_show_my_event, get_kb_show_speakers
from utils import Registration, output_events, output_my_event, TechSupport, AskSpeaker
from database import add_user, get_all_table, add_user_event, add_user_role, get_my_events, get_raffle_on_event, get_user_role

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

    raffle = await get_raffle_on_event(events[position][0])
    response = output_events(events, raffle, position)

    keyboard = await get_kb_show_event(position, len(events)-1)
    await callback.message.answer(response, reply_markup=keyboard)
    await callback.answer()

async def update_menu_events(callback: CallbackQuery, events: list, position: int):
    logger.info(f"Обновление меню мероприятий")

    raffle = await get_raffle_on_event(events[position][0])
    response = output_events(events, raffle, position)
    
    keyboard = await get_kb_show_event(position, len(events)-1)
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer()

@user_router.callback_query(F.data.startswith("next_event"))
async def get_next_event(callback: CallbackQuery):
    position = int(callback.data.split("_")[-1]) + 1
    logger.info(f"Вывод мероприятия: {position}")

    data = await get_all_table("schedule")
    await callback.answer()
    await update_menu_events(callback, data, position)

@user_router.callback_query(F.data.startswith("prev_event"))
async def get_next_event(callback: CallbackQuery):
    position = int(callback.data.split("_")[-1]) - 1
    logger.info(f"Вывод мероприятия: {position}")

    data = await get_all_table("schedule")
    await callback.answer()
    await update_menu_events(callback, data, position)

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
        await callback.message.answer("Не удалось записаться на мероприятие. Возможно вы уже на него записаны.")

    await callback.answer()

@user_router.callback_query(F.data == "get_qr")
async def show_my_events(callback: CallbackQuery):
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запрашивает qr")
    events = await get_my_events(user_id)

    if not events:
        logger.info(f"Список мероприятий пользователя {user_id} пуст")
        await callback.message.answer("Вы пока не записаны ни на одно мероприятие")
        await callback.answer()
        return
    
    position = 0
    response = output_my_event(events, position)
    event_id = events[position][0]
    keyboard = await get_kb_show_my_event(position, len(events) - 1, event_id)
    logger.info(f"Вывод меропртиятия с позицией: {position}")

    await callback.message.answer(response, reply_markup=keyboard)
    await callback.answer()

async def update_menu_my_events(callback: CallbackQuery, position: int, events: list):
    logger.info(f"Вывод меропртиятия с позицией: {position}")
    
    response = output_my_event(events, position)
    event_id = events[position][0]
    keyboard = await get_kb_show_my_event(position, len(events) - 1, event_id)
    await callback.message.edit_text(response, reply_markup=keyboard)
    await callback.answer()

@user_router.callback_query(F.data.startswith("my_next_event"))
async def get_next_event(callback: CallbackQuery):
    position = int(callback.data.split("_")[-1]) + 1
    user_id = callback.from_user.id

    data = await get_my_events(user_id)
    await callback.answer()
    await update_menu_my_events(callback, position, data)

@user_router.callback_query(F.data.startswith("my_prev_event"))
async def get_next_event(callback: CallbackQuery):
    position = int(callback.data.split("_")[-1]) - 1
    user_id = callback.from_user.id

    data = await get_my_events(user_id)
    await callback.answer()
    await update_menu_my_events(callback, position, data)

@user_router.callback_query(F.data.startswith("get_qr"))
async def generate_qr(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[-1])
    
    user_id = callback.from_user.id
    qr_data = f"https://t.me/{bot_username}?start=ev_{user_id}_{event_id}"
    qr_img = qrcode.make(qr_data)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    file = BufferedInputFile(buf.read(), filename="user_qr.png")
    await callback.message.answer_photo(photo=file, caption="Твой уникальный QR-код")
    await callback.answer()

    logger.info(f"QR-код отправлен пользователю {user_id}")

@user_router.callback_query(F.data == "technical_support")
async def get_message_for_technical_support(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = callback.from_user.id
        logger.info(f"Пользователь {user_id} запрашивает отправку вопроса в техподдержку")

        await callback.message.answer("Отправьте сообщение для техподдержки")
        await state.set_state(TechSupport.waiting_for_message)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции get_message_for_technical_support(): {e}")

@user_router.message(TechSupport.waiting_for_message)
async def send_message_to_technical_support(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        user_role = await get_user_role(user_id)

        response = f'Вопрос от <a href="tg://user?id={user_id}">{user_role}</a>:\n{message.text}'

        await bot.send_message(chat_id=technical_support_chat, text=response, parse_mode="HTML")
        await message.answer("Сообщение в техподдержку было успешно отправлено!")

        await state.clear()
        logger.info(f"Пользователь с ID {user_id} успешно отправил сообщение в техподдержку")
    except Exception as e:
        logger.error(f"Ошибка в функции send_message_to_technical_support(): {e}")

@user_router.callback_query(F.data == "ask_speaker")
async def show_speakers(callback: CallbackQuery):
    try:
        logger.info(f"Пользователь с ID {callback.from_user.id} запрашивает отпрвку вопроса спикеру")

        speakers = await get_all_table("speakers")
        kb = await get_kb_show_speakers(speakers)
        await callback.message.answer("Выберете спикера для обращения:", reply_markup=kb)

    except Exception as e:
        logger.error(f"Ошибка в функции show_speakers(): {e}")

@user_router.callback_query(F.data.startswith("speak:"))
async def ask_speaker(callback: CallbackQuery, state: FSMContext):
    try:
        _, speaker_id, speaker_name = callback.data.split(":", 2)
        logger.info(f"Вопрос спикеру с ID {speaker_id}")
        await state.update_data(speaker_name=speaker_name)

        await callback.message.answer("Отправьте вопрос")
        await state.set_state(AskSpeaker.waiting_for_message)
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в функции ask_speaker(): {e}")

@user_router.message(AskSpeaker.waiting_for_message)
async def get_question(message: Message, state: FSMContext):
    try:
        data = await state.get_data()

        await bot.send_message(chat_id=speakers_chat, text=f"Вопрос к спикеру {data["speaker_name"]}:\n{message.text}")
        await message.answer("Вопрос к спикеры был успешно отправлен")
    except Exception as e:
        logger.error(f"Ошибка в функции get_question(): {e}")