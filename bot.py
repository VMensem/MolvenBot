import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import vk_api
from aiogram import Bot, Dispatcher
from aiogram.types import InputFile
import logging

# ---------------- CONFIG ---------------- #
DISCORD_TOKEN = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
GUILD_ID = 1413563581592764500
DISCORD_CHANNEL_ID = 1413563583966613588
ALLOWED_USERS = [741774083355836478]  # сюда ID админов

TG_TOKEN = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHAT_ID = -1003091449025

VK_TOKEN = "vk1.a.LZnqNzchEADk_n27uAHk6PlqhY0kDuvjBV3T321R-iBahhcKyvZ2-G4QgdNv62bI9WwgZxNSYzbc17kkNaUdbGAA6Q4Alpn1gxo8ZQitMotmFMEKZFB9Wcy_e0IhDIZJN6p3pFBBSPr7SmZ5SuFgPvkM0jLRVoSG3uEfBTUAk-HU4uAGoYM7nbgyjNrLOHpUkVGM5S6N6wSEvYd2TEDhvQ"
VK_GROUP_ID = 209873316

# ---------------- LOGGING ---------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("molven")

# ---------------- TELEGRAM ---------------- #
tg_bot = Bot(token=TG_TOKEN)
tg_dp = Dispatcher(tg_bot)

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
