# bot.py
import os
import logging
import threading
import requests
import discord
from discord import app_commands
from discord.ext import commands
from aiogram import Bot as TgBot
from aiogram.enums import ParseMode
import flask

# ------------ НАСТРОЙКИ (подставь свои) ------------
APPLICATION_ID = 1413607342775468174      # ID приложения/бота из DevPortal
DISCORD_TOKEN = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
GUILD_ID = 123456789012345678        # ID твоего сервера

TG_TOKEN = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHAT_ID = -1003091449025               # чат/канал для новостей

VK_TOKEN = "vk1.a.LZnqNzchEADk_n27uAHk6PlqhY0kDuvjBV3T321R-iBahhcKyvZ2-G4QgdNv62bI9WwgZxNSYzbc17kkNaUdbGAA6Q4Alpn1gxo8ZQitMotmFMEKZFB9Wcy_e0IhDIZJN6p3pFBBSPr7SmZ5SuFgPvkM0jLRVoSG3uEfBTUAk-HU4uAGoYM7nbgyjNrLOHpUkVGM5S6N6wSEvYd2TEDhvQ"
VK_GROUP_ID = 209873316  
# ----------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("molven")

# Discord intents
intents = discord.Intents.default()
intents.message_content = True  # нужен, если хочешь видеть содержимое обычных сообщений

# Создаём бота с application_id (исправляет ошибку sync)
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=APPLICATION_ID
)
tree = bot.tree

# ------------------ ПОСТИНГ ------------------------
def post_to_telegram(text: str):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"})
        if not r.ok:
            logger.error("TG error %s", r.text)
    except Exception as e:
        logger.exception("TG posting failed: %s", e)

def post_to_vk(text: str):
    try:
        url = "https://api.vk.com/method/wall.post"
        payload = {
            "owner_id": f"-{VK_GROUP_ID}",
            "from_group": 1,
            "message": text,
            "access_token": VK_TOKEN,
            "v": "5.199"
        }
        r = requests.post(url, data=payload).json()
        if "error" in r:
            logger.error("VK error %s", r)
    except Exception as e:
        logger.exception("VK posting failed: %s", e)

async def post_to_discord_channel(text: str, interaction: discord.Interaction):
    await interaction.channel.send(text)

async def post_everywhere(text: str, interaction: discord.Interaction):
    # Discord
    await post_to_discord_channel(text, interaction)
    # Telegram / VK
    threading.Thread(target=lambda: post_to_telegram(text), daemon=True).start()
    threading.Thread(target=lambda: post_to_vk(text), daemon=True).start()

# ---------------- SLASH-КОМАНДЫ --------------------
@tree.command(name="text", description="Отправить текст в текущий канал")
@app_commands.describe(content="Что отправить")
async def text_cmd(interaction: discord.Interaction, content: str):
    await interaction.response.send_message("Отправляю…", ephemeral=True)
    await interaction.channel.send(content)

@tree.command(name="news", description="Постинг во все сервисы")
@app_commands.describe(content="Текст новости")
async def news_cmd(interaction: discord.Interaction, content: str):
    await interaction.response.send_message("Публикую новость…", ephemeral=True)
    await post_everywhere(content, interaction)

# --------------- ON_READY --------------------------
@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)         # синхронизируем только для одного сервера
        logger.info("Slash-команды синхронизированы для guild %s", GUILD_ID)
    except Exception as e:
        logger.exception("Ошибка синхронизации команд: %s", e)
    logger.info("Бот вошёл как %s", bot.user)

# ----------------- FLASK HEALTH --------------------
app = flask.Flask(__name__)

@app.route("/")
def health():
    return "OK"

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ------------------- MAIN --------------------------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(DISCORD_TOKEN)
