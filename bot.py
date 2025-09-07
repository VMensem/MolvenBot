# bot.py
import os
import asyncio
import threading
import logging

import discord
from discord import Intents
from discord.ext import commands

import vk_api
import requests

# ---- Telegram (aiogram 3.x) ----
from aiogram import Bot as TgBot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

# ---------- НАСТРОЙКИ ----------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"          # вставь свой НОВЫЙ токен
DISCORD_CHANNEL = 1413563583966613588   # id канала (можно None)

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602  # id группы ВКонтакте (без минуса)

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"          # токен бота Telegram
TG_CHANNEL      = "@MolvenRP"             # username канала Telegram (с @)
CREATOR_ID      = 1951437901            # только этот id может писать комманды в ТГ

# ---------- Discord ----------
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Discord: {bot.user} запущен")
    try:
        synced = await bot.tree.sync()
        print(f"Slash команд синхронизировано: {len(synced)}")
    except Exception as e:
        print(f"Sync error: {e}")

# ---- Discord команды ----
@bot.tree.command(name="ping", description="Проверка бота")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)

@bot.tree.command(name="news", description="Опубликовать новость в Discord + VK + Telegram")
async def news(interaction: discord.Interaction, text: str):
    await interaction.response.defer()

    # ---- Discord пост ----
    channel = bot.get_channel(DISCORD_CHANNEL) if DISCORD_CHANNEL else interaction.channel
    if channel:
        await channel.send(f"📢 Molven RolePlay:\n{text}")

    # ---- ВКонтакте ----
    try:
        vk = vk_api.VkApi(token=VK_TOKEN)
        vk.method("wall.post", {
            "owner_id": -VK_GROUP_ID,
            "from_group": 1,
            "message": text
        })
        print("Новость отправлена в VK")
    except Exception as e:
        print("VK ошибка:", e)

    # ---- Telegram ----
    try:
        await tg_bot.send_message(chat_id=TG_CHANNEL, text=f"📢 Molven RolePlay:\n{text}")
        print("Новость отправлена в Telegram")
    except Exception as e:
        print("TG ошибка:", e)

    await interaction.followup.send("Новость опубликована!")

# ---------- Telegram ----------
tg_bot = TgBot(
    TG_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

@dp.message(Command("start"))
async def tg_start(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    await message.answer("Привет! Доступны команды: /news <текст>")

@dp.message(Command("news"))
async def tg_news(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    text = message.text.partition(" ")[2].strip()
    if not text:
        await message.answer("Напиши текст после /news")
        return

    # Discord
    if DISCORD_CHANNEL:
        channel = bot.get_channel(DISCORD_CHANNEL)
        if channel:
            await channel.send(f"📢 Molven RolePlay:\n{text}")

    # VK
    try:
        vk = vk_api.VkApi(token=VK_TOKEN)
        vk.method("wall.post", {"owner_id": -VK_GROUP_ID, "from_group": 1, "message": text})
    except Exception as e:
        print("VK ошибка:", e)

    # Telegram канал
    await tg_bot.send_message(chat_id=TG_CHANNEL, text=f"📢 Molven RolePlay:\n{text}")
    await message.answer("Новость отправлена во все каналы")

# ---------- Flask (для Render, ping) ----------
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------- Запуск ----------
async def run_telegram():
    await dp.start_polling(tg_bot)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()      # Flask web
    threading.Thread(target=lambda: asyncio.run(run_telegram())).start()  # Telegram
    bot.run(DISCORD_TOKEN)
