from aiogram import Bot
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("BOT_TOKEN")

bot = Bot(token=token)
bot_username = os.getenv("BOT_USERNAME")