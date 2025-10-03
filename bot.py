from flask import Flask
import threading
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import vk_api
from aiogram import Bot
import logging
import os

# ---------------- CONFIG ---------------- #
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
ALLOWED_USERS = list(map(int, os.getenv("DISCORD_ALLOWED_USERS", "").split(",")))

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = int(os.getenv("TG_CHAT_ID", 0))

VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", 0))

# ---------------- LOGGING ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("molven")

# ---------------- TELEGRAM ---------------- #
tg_bot = Bot(token=TG_TOKEN)

async def send_to_telegram(text: str):
    try:
        await tg_bot.send_message(TG_CHAT_ID, text)
        logger.info("Сообщение отправлено в Telegram")
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")

# ---------------- VK ---------------- #
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

def send_to_vk(text: str):
    try:
        vk.wall.post(owner_id=-VK_GROUP_ID, message=text)
        logger.info("Сообщение опубликовано в VK")
    except Exception as e:
        logger.error(f"Ошибка отправки в VK: {e}")

# ---------------- DISCORD ---------------- #
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

async def post_to_services(text: str):
    await send_to_telegram(text)
    send_to_vk(text)
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(text)
    else:
        logger.error("Канал Discord не найден!")

# ---------------- COMMANDS ---------------- #
@tree.command(name="news", description="Опубликовать новость ВК/ТГ/ДС")
async def news(interaction: discord.Interaction, text: str):
    if interaction.user.id not in ALLOWED_USERS:
        await interaction.response.send_message("У тебя нет прав для публикации!", ephemeral=True)
        return

    # Ответ сразу, чтобы interaction не таймаутился
    await interaction.response.send_message("Публикуем новость...", ephemeral=True)

    try:
        await post_to_services(text)
    except Exception as e:
        logger.error(f"Ошибка при публикации новости: {e}")

@tree.command(name="text", description="Отправить текст в чат")
async def text_cmd(interaction: discord.Interaction, text: str):
    if interaction.user.id not in ALLOWED_USERS:
        await interaction.response.send_message("У тебя нет прав для отправки текста!", ephemeral=True)
        return

    await interaction.channel.send(text)
    await interaction.response.send_message("Текст отправлен!", ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f"Бот вошёл как {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    logger.info("Команды синхронизированы!")

# ---------------- RUN DISCORD ---------------- #
async def discord_runner():
    await bot.start(DISCORD_TOKEN)

def start_asyncio_loop():
    asyncio.run(discord_runner())

# ---------------- FLASK ---------------- #
app = Flask(__name__)

@app.route("/")
def home():
    return "Бот работает!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ---------------- START ---------------- #
if __name__ == "__main__":
    # Flask в отдельном потоке
    threading.Thread(target=run_flask).start()
    # Discord в главном потоке
    start_asyncio_loop()
