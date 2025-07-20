import asyncio
from aiogram import Dispatcher

from bot import bot, bot_username
from handlers.user_handler import user_router
from handlers.admin_handler import admin_router
from handlers.start_handler import start_router
from database import init_db

dp = Dispatcher()

dp.include_routers(start_router, user_router, admin_router)

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())