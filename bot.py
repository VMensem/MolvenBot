# bot.py
import os
import threading
import logging
import requests
from flask import Flask

import discord
from discord import app_commands
from discord.ext import commands

# ================== CONFIG ==================
DISCORD_TOKEN = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
GUILD_ID = 123456789012345678        # ID твоего сервера

TG_TOKEN = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHAT_ID = -1003091449025               # чат/канал для новостей

VK_TOKEN = "vk1.a.LZnqNzchEADk_n27uAHk6PlqhY0kDuvjBV3T321R-iBahhcKyvZ2-G4QgdNv62bI9WwgZxNSYzbc17kkNaUdbGAA6Q4Alpn1gxo8ZQitMotmFMEKZFB9Wcy_e0IhDIZJN6p3pFBBSPr7SmZ5SuFgPvkM0jLRVoSG3uEfBTUAk-HU4uAGoYM7nbgyjNrLOHpUkVGM5S6N6wSEvYd2TEDhvQ"
VK_GROUP_ID = 209873316  
# =============================================

logging.basicConfig(level=logging.INFO)

# ---------- Healthcheck для Render ----------
app = Flask(__name__)
@app.route("/")
def index():
    return "OK"

def run_healthcheck():
    app.run(host="0.0.0.0", port=5000)

# ---------- Discord Bot ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


# ===== Служебные функции =====
async def post_to_telegram(text: str):
    """Отправка в Telegram"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text})
    if not r.ok:
        logging.error("Telegram error: %s", r.text)

async def post_to_vk(text: str):
    """Пост на стену ВК"""
    r = requests.post(
        "https://api.vk.com/method/wall.post",
        params={
            "owner_id": -VK_GROUP_ID,
            "message": text,
            "access_token": VK_TOKEN,
            "v": "5.131",
        },
    )
    resp = r.json()
    if "error" in resp:
        logging.error("VK error: %s", resp)

async def post_everywhere(text: str):
    """В TG и VK (Discord выводим самим командой)"""
    await post_to_telegram(text)
    await post_to_vk(text)


# ===== Slash-команды =====
@tree.command(name="text", description="Просто отправить текст в этот канал")
@app_commands.describe(message="Текст для публикации")
async def text_cmd(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)

@tree.command(name="news", description="Опубликовать новость в Discord + TG + VK")
@app_commands.describe(message="Текст новости")
async def news_cmd(interaction: discord.Interaction, message: str):
    # Discord сразу отвечает в канал
    await interaction.response.send_message(f"Новость: {message}")
    # Телеграм + ВК
    await post_everywhere(message)


# ===== События =====
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    # Полная синхронизация команд
    await tree.sync(guild=guild)
    logging.info("Bot is online, commands synced for guild %s", GUILD_ID)


# ===== main =====
if __name__ == "__main__":
    # Запускаем health-сервер, чтобы Render видел порт
    threading.Thread(target=run_healthcheck, daemon=True).start()

    bot.run(DISCORD_TOKEN)
