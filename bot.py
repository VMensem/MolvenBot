import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import vk_api
from aiogram import Bot, Dispatcher
from aiogram.types import InputFile
import logging
import os

# ---------------- CONFIG ---------------- #
# Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
ALLOWED_USERS = list(map(int, os.getenv("DISCORD_ALLOWED_USERS", "").split(",")))

# Telegram
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = int(os.getenv("TG_CHAT_ID", 0))

# VK
VK_TOKEN = os.getenv("VK_TOKEN")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", 0))

# ---------------- LOGGING ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("molven")

# ---------------- TELEGRAM ---------------- #
tg_bot = Bot(token=TG_TOKEN)
tg_dp = Dispatcher()

async def send_to_telegram(text):
    try:
        await tg_bot.send_message(TG_CHAT_ID, text)
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")

# ---------------- VK ---------------- #
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

def send_to_vk(text):
    try:
        vk.wall.post(owner_id=-VK_GROUP_ID, message=text)
    except Exception as e:
        logger.error(f"Ошибка отправки в VK: {e}")

# ---------------- DISCORD ---------------- #
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

async def post_to_services(text):
    # Отправка во все сервисы
    await send_to_telegram(text)
    send_to_vk(text)
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(text)
    else:
        logger.error("Канал Discord не найден!")

# ---------------- DISCORD COMMANDS ---------------- #
@tree.command(name="news", description="Опубликовать новость на всех сервисах")
async def news(interaction: discord.Interaction, text: str):
    if interaction.user.id not in ALLOWED_USERS:
        await interaction.response.send_message("У тебя нет прав для публикации!", ephemeral=True)
        return
    await post_to_services(text)
    await interaction.response.send_message("Новость опубликована!", ephemeral=True)

@tree.command(name="text", description="Отправить текст в канал Discord")
async def text_cmd(interaction: discord.Interaction, text: str):
    if interaction.user.id not in ALLOWED_USERS:
        await interaction.response.send_message("У тебя нет прав для отправки текста!", ephemeral=True)
        return
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if channel:
        await channel.send(text)
        await interaction.response.send_message("Текст отправлен!", ephemeral=True)
    else:
        await interaction.response.send_message("Канал Discord не найден!", ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f"Бот вошёл как {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    await tree.sync(guild=guild)
    logger.info("Команды синхронизированы!")

# ---------------- RUN ---------------- #
async def main():
    await bot.start(DISCORD_TOKEN)

async def start_telegram():
    await tg_dp.start_polling()

async def runner():
    await asyncio.gather(main(), start_telegram())

if __name__ == "__main__":
    asyncio.run(runner())
