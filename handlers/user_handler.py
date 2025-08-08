from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging
from io import BytesIO
import qrcode
from aiogram.types.input_file import BufferedInputFile

from bot import bot_username, bot, technical_support_chat, speakers_chat, networking_chat_name, networking_chat_id
from keyboards.inline_keyboards import phone_kb, keyboard_user, get_kb_show_event, get_kb_show_my_event, get_kb_show_speakers, networking_builder_link_note_kb, networking_field_kb
from keyboards.inline_keyboards import networking_yes_no_kb, networking_send_cancel_kb
from utils import Registration, output_events, output_my_event, TechSupport, AskSpeaker, CreateNoteNetworkingChat, MessageLike
from database import add_user, get_all_table, add_user_event, add_user_role, get_my_events, get_raffle_on_event, get_user_role
from .start_handler import start_handler

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
        await callback.answer()

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

        await bot.send_message(
                            chat_id=speakers_chat, 
                            text=f"Вопрос к спикеру {data["speaker_name"]} от <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a>:\n{message.text}",
                            parse_mode="HTML")
        await message.answer("Вопрос к спикеру был успешно отправлен")
    except Exception as e:
        logger.error(f"Ошибка в функции get_question(): {e}")

@user_router.callback_query(F.data == "networking_chat")
async def networking_chat(callback: CallbackQuery):
    try:
        logger.info(f"Пользователь с ID {callback.from_user.id} переходит в нетворкинг чат")

        await callback.message.answer("Выберите опцию",reply_markup=networking_builder_link_note_kb)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции networking_chat(): {e}")

@user_router.callback_query(F.data == "get_link")
async def get_link_on_networking_chat(callback: CallbackQuery):
    try:
        logger.info(f"Пользователь с ID {callback.from_user.id} запрошивает ссылку на нетворкинг чат")

        await callback.message.answer(f'[Ссылка на чат](https://t.me/{networking_chat_name})', parse_mode="MarkdownV2")
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции get_link_on_networking_chat(): {e}")

@user_router.callback_query(F.data == "create_note")
async def create_note_for_networking_chat(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Пользователь c ID {callback.from_user.id} начинает создание карточки")

        await callback.message.answer("Введите ФИО")
        await state.set_state(CreateNoteNetworkingChat.waiting_for_full_name)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции create_note_for_networking_chat(): {e}")

@user_router.message(CreateNoteNetworkingChat.waiting_for_full_name)
async def get_full_name_for_name(message: Message, state: FSMContext):
    try:
        logger.info("Получено ФИО пользователя")

        await state.update_data(full_name=message.text)
        await message.answer("Выберете сферу вашей деятельности:", reply_markup=networking_field_kb)
    except Exception as e:
        logger.error(f"Ошибка в функции get_full_name_for_name(): {e}")

@user_router.callback_query(F.data.startswith("field"))
async def get_field_networking_chat(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info("Получена сфера деятельности пользователя")

        field = callback.data.split(':')[1]
        await state.update_data(field=field)
        await state.set_state(CreateNoteNetworkingChat.waiting_for_description)

        await callback.message.answer("Отправьте описание о себе")
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции get_field_networking_chat(): {e}")

@user_router.message(CreateNoteNetworkingChat.waiting_for_description)
async def get_description_networking_chat(message: Message, state: FSMContext):
    try:
        logger.info("Получено описание о пользователе")

        await state.update_data(description=message.text)
        await message.answer("Будет ли у вас фотография?", reply_markup=networking_yes_no_kb)
    except Exception as e:
        logger.error(f"Ошибка в функции get_description_networking_chat(): {e}")

@user_router.callback_query(F.data == "image_necessary_net")
async def add_image_in_note(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info("Будет добавлена фотография в карточку")

        await callback.message.answer("Отправьте изображение")
        await state.set_state(CreateNoteNetworkingChat.waiting_for_photo)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции add_image_in_note(): {e}")

@user_router.callback_query(F.data == "image_not_necessary_net")
async def send_note_onlytext(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info("В карточке не будет фотографии")

        user_id = callback.from_user.id
        data = await state.get_data()
        await bot.send_message(
                                chat_id=user_id, 
                                text=(
                                        f"✨ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✨\n"
                                        f"🧑‍💻 <b>Профиль участника</b>\n\n"
                                        f"🪪 <b>ФИО:</b> <a href='tg://user?id={user_id}'>{data['full_name']}</a>\n"
                                        f"🏷️ <b>Сфера:</b> {data['field']}\n\n"
                                        f"📌 <b>О себе:</b>\n"
                                        f"┗ {data['description']}\n\n"
                                        f"✨ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✨"
                                    ),
                                parse_mode="HTML"
        )
        await callback.message.answer("Отправлено будет только сообщение без фотографии! Подтвердите отправку", reply_markup=networking_send_cancel_kb)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции send_note_onlytext(): {e}")

@user_router.message(CreateNoteNetworkingChat.waiting_for_photo)
async def send_note_with_image(message: Message, state: FSMContext):
    try:
        logger.info(f"В карточку добавлено фото")

        photo = message.photo[-1]
        await state.update_data(photo_id=photo.file_id)
        
        user_id = message.from_user.id
        data = await state.get_data()
        await bot.send_photo(
            chat_id=message.from_user.id,
            photo=data["photo_id"],
            caption=(
                        f"✨ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✨\n"
                        f"🧑‍💻 <b>Профиль участника</b>\n\n"
                        f"🪪 <b>ФИО:</b> <a href='tg://user?id={user_id}'>{data['full_name']}</a>\n"
                        f"🏷️ <b>Сфера:</b> {data['field']}\n\n"
                        f"📌 <b>О себе:</b>\n"
                        f"┗ {data['description']}\n\n"
                        f"✨ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✨"
                    ),
            parse_mode="HTML"
        )
        await message.answer("Фотография получена! Подтвердите отправку", reply_markup=networking_send_cancel_kb)
    except Exception as e:
        logger.error(f"Ошибка в функции send_note_with_image(): {e}")

@user_router.callback_query(F.data == "send_note")
async def send_note(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = callback.from_user.id

        if "photo_id" in data:
            await bot.send_photo(
                chat_id=networking_chat_id,
                photo=data["photo_id"],
                caption=(
                            f"✨ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✨\n"
                            f"🧑‍💻 <b>Профиль участника</b>\n\n"
                            f"🪪 <b>ФИО:</b> <a href='tg://user?id={user_id}'>{data['full_name']}</a>\n"
                            f"🏷️ <b>Сфера:</b> {data['field']}\n\n"
                            f"📌 <b>О себе:</b>\n"
                            f"┗ {data['description']}\n\n"
                            f"✨ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✨"
                        ),
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=networking_chat_id, 
                text=(
                        f"✨ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✨\n"
                        f"🧑‍💻 <b>Профиль участника</b>\n\n"
                        f"🪪 <b>ФИО:</b> <a href='tg://user?id={user_id}'>{data['full_name']}</a>\n"
                        f"🏷️ <b>Сфера:</b> {data['field']}\n\n"
                        f"📌 <b>О себе:</b>\n"
                        f"┗ {data['description']}\n\n"
                        f"✨ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✨"
                    ),
                parse_mode="HTML"
            )
        await callback.message.answer("Карточка успешно отправлена в чат!")
        await callback.answer()
        logger.info(f"Пользователь {callback.from_user.id} успешно отправил карточку в чат")
        
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в функции send_note(): {e}")

@user_router.callback_query(F.data == "cancel_note")
async def cancel_note(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info("Отмена отправки карточки")
        await state.clear()
        
        await start_handler(MessageLike(callback), state)
        await callback.answer("❌ Отправка карточки отменена")
    except Exception as e:
        logger.error(f"Ошибка в функции cancel_note(): {e}")