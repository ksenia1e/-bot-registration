from aiogram import Bot
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("BOT_TOKEN")

bot = Bot(token=token)
bot_username = os.getenv("BOT_USERNAME")

technical_support_chat = os.getenv("TECHNICAL_CHAT_SUPPORT_ID")
speakers_chat = os.getenv("SPEAKERS_CHAT")
networking_chat_name = os.getenv("NETWORKING_CHAT_NAME")
networking_chat_id = os.getenv("NETWORKING_CHAT_ID")