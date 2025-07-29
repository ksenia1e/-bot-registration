from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand
import random

class Registration(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()

class AddOrganizer(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_full_name = State()

async def set_bot_commands(bot):
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="admin", description="Админ-панель"),
    ]
    await bot.set_my_commands(commands)

async def get_random_user(users):
    return random.choice(users)