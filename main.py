import asyncio
from aiogram import Dispatcher
import logging

from bot import bot
from utils import set_bot_commands
from handlers.user_handler import user_router
from handlers.admin_handler import admin_router
from handlers.start_handler import start_router
from database import init_db

dp = Dispatcher()

dp.include_routers(start_router, user_router, admin_router)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Бот запускается...")
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await set_bot_commands(bot)
    logger.info("Бот запущен. Ожидание сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")