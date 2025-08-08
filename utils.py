from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand
import random

class Registration(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_phone = State()

class AddOrganizer(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_full_name = State()

class Broadcast(StatesGroup):
    waiting_for_photo = State()
    waiting_for_photo_confirm = State()
    waiting_for_confirmation = State()

class TechSupport(StatesGroup):
    waiting_for_message = State()

class AskSpeaker(StatesGroup):
    waiting_for_message = State()

class CreateNoteNetworkingChat(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_description = State()
    waiting_for_photo = State()

class MessageLike:
    def __init__(self, callback):
        self.chat = callback.message.chat
        self.from_user = callback.from_user
        self.answer = callback.message.answer
        self.bot = callback.bot
        self.message_id = callback.message.message_id
        self.text = "/start"  # добавляем text, если хендлер его требует

async def set_bot_commands(bot):
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="admin", description="Админ-панель"),
    ]
    await bot.set_my_commands(commands)

async def get_random_user(users):
    return random.choice(users)

def get_values(data: list[dict]):
    return [[v for k, v in item.items() if k != 'ID мероприятия'] for item in data]

def output_events(events: list, raffle: list, position: int):
    event_row = events[position]
    event_text = (
        f"🎯 **{event_row[1]}**\n"
        f"📅 {event_row[2]}\n"
        f"🕒 {event_row[3]} - {event_row[4]}\n"
        f"📍 {event_row[5]}\n"
        f"📌 {event_row[6]}\n"
        f"───────────────────\n"
        f"Мероприятие {position+1}/{len(events)}\n\n"
    )

    raffle_text = "\n".join(
        f"🏆 **{row[1]}**\n"
        f"📅 {row[2]}\n"
        f"⏰ {row[3]} – {row[4]}\n"
        f"💰 Призы: {row[5]}\n"
        f"────────────────────"
        for row in raffle
    )

    return event_text + "\n🎁 Розыгрыши:\n" + raffle_text

def output_my_event(events: list, position: int):
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