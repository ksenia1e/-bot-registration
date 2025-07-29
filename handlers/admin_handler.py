import qrcode
import asyncio
from io import BytesIO
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_file import BufferedInputFile
import logging

from utils import AddOrganizer, get_random_user
from bot import bot, bot_username
from keyboards.inline_keyboards import keyboard_admin, keyboard_qr, builder_show_organizers
from database import get_user_role, get_users, add_organizer_, get_number_of_users_, get_organizers, delete_organizer_, get_users_id_name

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
        await message.answer("Организатор успешно добавлен")
        logger.info(f"Организатор {data['user_id']} успешно добавлен админом {message.from_user.id}")
    except Exception as e:
        await message.answer(f"Ошибка в добавлении: {e}")
        logger.error(f"Ошибка при добавлении организатора: {e}")
    await state.clear()


@admin_router.callback_query(F.data == "broadcast")
async def send_newsletter(callback: CallbackQuery):
    text = "Всех приветствую, для быстрой регистрации на мероприятии покажите QR-код, который можно получить по кнопке ниже"
    users = await get_users()

    logger.info(f"Админ {callback.from_user.id} начал рассылку для {len(users)} пользователей")

    for row in users:
        try:
            await bot.send_message(chat_id=row[0], text=text, reply_markup=keyboard_qr)
        except Exception as e:
            logger.warning(f"Ошибка при отправке пользователю {row[0]}: {e}")

    await callback.answer("Рассылка завершена.")
    logger.info(f"Рассылка завершена админом {callback.from_user.id}")


@admin_router.callback_query(F.data == "get_qr")
async def generate_qr(call: CallbackQuery):
    user = call.from_user
    qr_data = f"https://t.me/{bot_username}?start={user.id}"
    qr_img = qrcode.make(qr_data)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    file = BufferedInputFile(buf.read(), filename="user_qr.png")
    await call.message.answer_photo(photo=file, caption="Твой уникальный QR-код")
    await call.answer()

    logger.info(f"QR-код отправлен пользователю {user.id}")


@admin_router.callback_query(F.data == "count_users")
async def get_number_of_users(callback: CallbackQuery):
    num = await get_number_of_users_()
    await callback.message.answer(f"Количество зарегистрированных: {num}")
    logger.info(f"Админ {callback.from_user.id} запросил количество пользователей: {num}")

@admin_router.callback_query(F.data == "delete_org")
async def show_organizers(callback: CallbackQuery):
    organizers = await get_organizers()

    for user_id, full_name in organizers:
        builder_show_organizers.button(
            text=full_name,
            callback_data=f"org:{user_id}"
        )
    await callback.message.answer("Выберите организатора на удаление", reply_markup=builder_show_organizers.as_markup())

    logger.info(f"Админ {callback.from_user.id} запросил вывод организаторов на удаление")

@admin_router.callback_query(F.data.startswith("org:"))
async def delete_organizer(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    await delete_organizer_(user_id)

    await callback.message.answer(f"Организатор удален")
    logger.info(f"Удален организатор {user_id}")

@admin_router.callback_query(F.data == "hold_draw")
async def hold_draw(callback: CallbackQuery):
    await callback.message.answer("Розыгрыш начат...")
    logger.info(f"Админ {callback.from_user.id} начал розыгрыш для {len(users)} пользователей")

    users = await get_users_id_name()
    if not users:
        await callback.message.answer("Нет пользователей для розыгрыша")
        logger.info("Нет пользователей для розыгрыша")
        return

    text1 = "🎉Сейчас будет проведен розыгрыш, результаты будут через 5 секунд..."

    for user_id, _ in users:
        try:
            await bot.send_message(chat_id=user_id, text=text1, reply_markup=keyboard_qr)
        except Exception as e:
            logger.warning(f"Ошибка при отправке пользователю {user_id}: {e}")

    await asyncio.sleep(5)
    winner_user_id, winner_user_name = await get_random_user(users)

    text2 = f"**Результаты розыгрыша**\n 🏆 Победитель: {winner_user_name or 'Аноним'} (ID: {winner_user_id})"

    for user_id, _ in users:
        try:
            await bot.send_message(chat_id=user_id, text=text2, reply_markup=keyboard_qr)
        except Exception as e:
            logger.warning(f"Ошибка при отправке пользователю {user_id}: {e}")
    
    await callback.message.answer("Розыгрыш завершен.")
    logger.info(f"Рассылка завершена админом {callback.from_user.id}")