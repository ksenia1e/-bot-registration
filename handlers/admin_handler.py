import asyncio
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import logging

from utils import AddOrganizer, get_random_user, get_values, Broadcast
from google_sheets import get_all_data
from bot import bot
from keyboards.inline_keyboards import keyboard_admin, get_kb_show_organozers, broadcast_yes_no_kb, broadcast_builder_send_cancel_kb
from database import get_user_role, get_users, add_organizer_, get_number_of_users_on_event, set_event_prize, get_all_table, add_speaker
from database import get_organizers, delete_organizer_, get_users_id_name, get_schedule, get_raffle, add_raffle, add_schedule, clear_table, add_user_role

admin_router = Router()
logger = logging.getLogger(__name__)

@admin_router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if await get_user_role(message.from_user.id) != "admin":
        await message.answer("Нет прав доступа")
        logger.warning(f"Пользователь {message.from_user.id} пытался получить доступ к админ-панели")
        return

    logger.info(f"Администратор {message.from_user.id} открыл панель администратора")
    await message.answer("Выберете опцию: ", reply_markup=keyboard_admin)


@admin_router.callback_query(F.data == "add_org")
async def add_organizer(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Админ {callback.from_user.id} начал добавление организатора")
    await callback.message.answer("Введите ID")
    await state.set_state(AddOrganizer.waiting_for_user_id)
    await callback.answer()


@admin_router.message(AddOrganizer.waiting_for_user_id)
async def add_user_id(message: Message, state: FSMContext):
    user_id = message.text.strip()
    await state.update_data(user_id=user_id)
    logger.info(f"Получен user_id: {user_id} от админа {message.from_user.id}")
    await message.answer("Введите ФИО")
    await state.set_state(AddOrganizer.waiting_for_full_name)


@admin_router.message(AddOrganizer.waiting_for_full_name)
async def add_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    await state.update_data(full_name=full_name)
    logger.info(f"Получено ФИО: {full_name} от админа {message.from_user.id}")

    data = await state.get_data()

    try:
        await add_organizer_(
            int(data["user_id"]),
            data["full_name"]
        )
        await add_user_role(
            int(data["user_id"]),
            "organizer"
        )

        await message.answer("Организатор успешно добавлен")
        logger.info(f"Организатор {data['user_id']} успешно добавлен админом {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка в добавлении: {e}")
        logger.error(f"Ошибка при добавлении организатора: {e}")
    await state.clear()

temp_data = {}

@admin_router.callback_query(F.data == "broadcast")
async def send_newsletter(callback: CallbackQuery, state: FSMContext):
    try:
        logger.info(f"Админ {callback.from_user.id} запрашивает рассылку")
        await callback.message.answer("Отправьте текст рассылки")
        await state.set_state(Broadcast.waiting_for_photo_confirm)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции send_newsletter(): {e}")

@admin_router.message(Broadcast.waiting_for_photo_confirm, F.text)
async def get_broadcast_content(message: Message, state: FSMContext):
    try:
        logger.info("В рассылку добавлен текст")
        await state.update_data(broadcast_text=message.text.strip())
        await message.answer("Необходимо ли отправить прикрепить фото к сообщению?", reply_markup=broadcast_yes_no_kb)
    except Exception as e:
        logger.error(F"Ошибка в функции get_broadcast_content(): {e}")

@admin_router.callback_query(F.data == "image_necessary")
async def attach_image(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.answer("Отправьте изображение")
        await state.set_state(Broadcast.waiting_for_photo)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в функции attach_image(): {e}")

@admin_router.message(Broadcast.waiting_for_photo)
async def attach_image(message: Message, state: FSMContext):
    try:
        logger.info(f"В рассылку будет добавлено фото")
        photo = message.photo[-1]
        await state.update_data(photo_id=photo.file_id)
        
        data = await state.get_data()
        await bot.send_photo(
            chat_id=message.from_user.id,
            photo=data["photo_id"],
            caption=data["broadcast_text"]
        )
        await message.answer("Фотография получена! Подтвердите отправку", reply_markup=broadcast_builder_send_cancel_kb)
    except Exception as e:
        logger.error(f"Ошибка в функции attach_image(): {e}")

@admin_router.callback_query(F.data == "image_not_necessary")
async def send_broadcast_onlytext(callback: CallbackQuery,  state: FSMContext):
    logger.info("В рассылку будет только текст")
    
    data = await state.get_data()
    await bot.send_message(chat_id=callback.from_user.id, text=data["broadcast_text"])
    await callback.message.answer("Отправлено будет только сообщение без фотографии! Подтвердите отправку", reply_markup=broadcast_builder_send_cancel_kb)
    await callback.answer()

@admin_router.callback_query(F.data == "send_broadcast")
async def send_broadcast(callback: CallbackQuery, state: FSMContext):
    try:
        users = await get_users()
        logger.info(f"Админ {callback.from_user.id} начал рассылку для {len(users)} пользователей")

        data = await state.get_data()

        if "photo_id" in data:
            for row in users:
                try:
                    await bot.send_photo(
                        chat_id=row[0],
                        photo=data["photo_id"],
                        caption=data["broadcast_text"]
                    )
                except Exception as e:
                    logger.warning(f"Ошибка при отправке пользователю с ID {row[0]}: {e}")

        else:
            for row in users:
                try:
                    await bot.send_message(chat_id=row[0], text=data["broadcast_text"])
                except Exception as e:
                    logger.warning(f"Ошибка при отправке пользователю с ID {row[0]}: {e}")

        await callback.message.answer("Рассылка успешко завершена!")
        await callback.answer()
        logger.info(f"Админ {callback.from_user.id} успешно завершил рассылку")
        
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в функции send_broadcast(): {e}")

@admin_router.callback_query(F.data == "count_users")
async def get_number_of_users(callback: CallbackQuery):
    try:
        events = await get_all_table("schedule")
        response = []

        if not events:
            logger.info("Таблица schedule пуста")
            callback.message.answer("Пока не проводится никаких мероприятий")
            callback.answer()

        for row in events:

            event_id = row[0]
            event_name = row[1]
            num = (await get_number_of_users_on_event(event_id))[0]

            response.append(
                f"На мероприятие {event_name} количество зарегистрированных: {num} \n"
                f"     -------------------     "
            )

        result = "\n".join(response)
        await callback.answer(result, show_alert=True)
        logger.info(f"Админ {callback.from_user.id} запросил количество пользователей: {num}")
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в функции get_number_of_users(): {e}")

@admin_router.callback_query(F.data == "delete_org")
async def show_organizers(callback: CallbackQuery):
    organizers = await get_organizers()

    kb = await get_kb_show_organozers(organizers)

    if not kb.inline_keyboard:
        await callback.message.answer("Список организаторов пуст")
    else:
        await callback.message.answer("Выберите организатора на удаление", reply_markup=kb)
    await callback.answer()
    logger.info(f"Админ {callback.from_user.id} запросил вывод организаторов на удаление")

@admin_router.callback_query(F.data.startswith("org:"))
async def delete_organizer(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    await delete_organizer_(user_id)

    await callback.message.answer(f"Организатор удален", reply_markup=ReplyKeyboardRemove())
    await callback.answer()
    logger.info(f"Удален организатор {user_id}")

@admin_router.callback_query(F.data == "hold_draw")
async def hold_draw(callback: CallbackQuery):
    try:
        await callback.message.answer("Розыгрыш начат...")
        users = await get_users_id_name()
        logger.info(f"Админ {callback.from_user.id} начал розыгрыш для {len(users)} пользователей")
        if not users:
            await callback.message.answer("Нет пользователей для розыгрыша")
            await callback.answer()
            logger.info("Нет пользователей для розыгрыша")
            return

        text1 = "🎉Сейчас будет проведен розыгрыш, результаты будут через 5 секунд..."

        for user_id, _ in users:
            try:
                await bot.send_message(chat_id=user_id, text=text1)
            except Exception as e:
                logger.warning(f"Ошибка при отправке пользователю {user_id}: {e}")

        await asyncio.sleep(5)
        winner_user_id, winner_user_name = await get_random_user(users)

        text2 = f"**Результаты розыгрыша**\n 🏆 Победитель: {winner_user_name or 'Аноним'} (ID: {winner_user_id})"

        for user_id, _ in users:
            try:
                await bot.send_message(chat_id=user_id, text=text2)
            except Exception as e:
                logger.warning(f"Ошибка при отправке пользователю {user_id}: {e}")
        
        await callback.message.answer("Розыгрыш завершен.")
        await callback.answer()
        logger.info(f"Рассылка завершена админом {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Ошибка в функции hold_draw(): {e}")

@admin_router.callback_query(F.data == "synchronization")
async def synchronization_db_and_gs(callback: CallbackQuery):
    try:
        await callback.message.answer("Начинаю синхронизацию базы данных и гугл таблицы")
        logger.info(f"Админ {callback.from_user.id} запрашивает синхронизацию базы данных и гугл таблиц")
        data_schedule = get_all_data(0)
        schedule = await get_schedule()
        flag = False

        if not schedule:
                logger.info("Таблица schedule пуста")
                for row in data_schedule:
                    try:
                        await add_schedule(
                            row['ID'],
                            row['Название'],
                            row['Дата'],
                            row['Время начала'],
                            row['Время окончания'],
                            row['Место'],
                            row['Описание']
                            )
                    except Exception as e:
                        logger.warning(f"Ошибка добавления в таблицу schedule: {e}")
                        await callback.message.answer("Ошибка синхронизации таблицы schedule")
                        await callback.answer()
                        return
                flag = True
                logger.info("Успешное обновление таблицы schedule")

        elif len(data_schedule[0].keys()) != len(schedule[0].keys()):
            logger.warning("Ошибка синхронизации schedule и гугл таблицы Schedule. Необходимо обновить гугл таблицу Schedule")
            await callback.message.answer("Ошибка синхронизации schedule и гугл таблицы Schedule. Необходимо обновить гугл таблицу Schedule")
            await callback.answer()
            return
        
        if not flag and get_values(data_schedule) != get_values(schedule):
            await clear_table("schedule")
            for row in data_schedule:
                try:
                    await add_schedule(
                        row['ID'],
                        row['Название'],
                        row['Дата'],
                        row['Время начала'],
                        row['Время окончания'],
                        row['Место'],
                        row['Описание']
                        )
                except Exception as e:
                    logger.warning(f"Ошибка добавления в таблицу schedule: {e}")
                    await callback.message.answer("Ошибка синхронизации таблицы schedule")
                    await callback.answer()
                    return
            logger.info("Успешное обновление таблицы schedule")
        
        raffle = await get_raffle()
        data_raffle = get_all_data(1)
        event_prize = await get_all_table("event_prize")
        flag = False

        if not raffle:
            logger.info("Таблица raffle пуста")
            for row in data_raffle:
                try:
                    await add_raffle(
                        row['ID'],
                        row['Название'],
                        row['Дата'],
                        row['Время начала'],
                        row['Время окончания'],
                        row['Призы']
                        )

                except Exception as e:
                    logger.warning(f"Ошибка добавления в таблицу raffle: {e}")
                    await callback.message.answer("Ошибка синхронизации таблицы raffle")
                    await callback.answer()
                    return
                
            flag = True
            await callback.message.answer("Успешная синхронизация таблицы raffle")

        elif len(data_raffle[0].keys()) - 1 != len(raffle[0].keys()):
            logger.warning("Ошибка синхронизации raffle и гугл таблицы Raffle. Необходимо обновить гугл таблицу Raffle")
            await callback.message.answer("Ошибка синхронизации raffle и гугл таблицы Raffle. Необходимо обновить гугл таблицу Raffle")
            await callback.answer()
            return
        
        if not flag and get_values(data_raffle) != get_values(raffle):
            await clear_table("raffle")
            for row in data_raffle:
                try:
                    await add_raffle(
                        row['ID'],
                        row['Название'],
                        row['Дата'],
                        row['Время начала'],
                        row['Время окончания'],
                        row['Призы']
                        )

                except Exception as e:
                    logger.warning(f"Ошибка добавления в таблицу raffle: {e}")
                    await callback.message.answer("Ошибка синхронизации таблицы raffle")
                    await callback.answer()
                    return
                
            logger.info("Успешное обновление таблицы raffle")
        
        google_event_prize = list((row['ID мероприятия'], row['ID']) for row in data_raffle)
        flag = False

        if not event_prize:
            logger.info("Таблица event_prize пустая")
            try:
                for row in google_event_prize:
                    await set_event_prize(row[0], row[1])

            except Exception as e:
                logger.warning(f"Ошибка добавления в таблицу event_prize: {e}")
                await callback.message.answer("Ошибка синхронизации таблицы мероприятия и лотереи")
                await callback.answer()
                return

            flag = True
            logger.info("Успешное обновление таблицы event_prize")

        if not flag and google_event_prize != event_prize:
            await clear_table("event_prize")

            try:
                for row in google_event_prize:
                    await set_event_prize(row[0], row[1])

            except Exception as e:
                logger.warning(f"Ошибка добавления в таблицу event_prize: {e}")
                await callback.message.answer("Ошибка синхронизации таблицы мероприятия и лотереи")
                await callback.answer()
                return
            
            logger.info("Успешное обновление таблицы event_prize")

        google_speakers = get_all_data(2)
        speakers = await get_all_table("speakers")
        flag = False

        if not speakers:
            logger.info("Таблица speakers пуста")
            try:
                for row in google_speakers:
                    await add_speaker(row["ID"], row["ФИО"])

                logger.info("Успешное обновление таблицы speakers")
                flag = True
            
            except Exception as e:
                logger.error(f"Ошибка обновления таблицы speakers: {e}")
                await callback.message.answer("Ошибка обновления таблицы speakers")
                await callback.answer()
                return

        elif len(google_speakers[0].keys()) != len(speakers[0]):
            logger.warning("Ошибка синхронизации speakers и гугл таблицы Speakers. Необходимо обновить гугл таблицу Speakers")
            await callback.message.answer("Ошибка синхронизации speakers и гугл таблицы Speakers. Необходимо обновить гугл таблицу Speakers")
            await callback.answer()
            return

        speakers = [[id, full_name] for row in speakers for (id, full_name) in [row]]

        if not flag and get_values(google_speakers) != speakers:
            try:
                for row in google_speakers:
                    await add_speaker(row["ID"], row["ФИО"])

                logger.info("Успешное обновление таблицы speakers")

            except Exception as e:
                logger.error(f"Ошибка обновления таблицы speakers: {e}")
                await callback.message.answer("Ошибка обновления таблицы speakers")
                await callback.answer()
                return

        await callback.message.answer("Синхронизация базы данных и гугл таблиц успешно завершена")
        await callback.answer()

        logger.info(f"Админ {callback.from_user.id} успешно завершил синхронизацию базы данных и гугл таблиц")

    except Exception as e:
        logger.error(f"Ошибка в функции synchronization_db_and_gs(): {e}")