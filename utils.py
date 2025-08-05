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

def get_values(dict: dict):
    return [list(d.values()) for d in dict]

def output_events(events: list, position: int):
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
    return response