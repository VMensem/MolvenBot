

# bot.py
import os
import threading
import asyncio
import logging
from typing import Optional

import discord
from discord import app_commands

from flask import Flask

import requests
from aiogram import Bot as TgBot, Dispatcher, types
from aiogram.enums import ParseMode

# -------------------- Настройки --------------------
# --------- Настройки ---------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"
CREATOR_ID      = 1951437901
# ----------------------------------------------------

logging.basicConfig(level=logging.INFO)

# -------------------- Discord --------------------
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f"Discord bot logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)


@tree.command(name="news", description="Опубликовать новость в Discord + VK + Telegram")
@app_commands.describe(text="Текст новости")
async def news(interaction: discord.Interaction, text: str):
    try:
        await interaction.response.send_message("📤 Публикую…", ephemeral=True)

        # Discord
        if DISCORD_CHANNEL:
            channel = bot.get_channel(DISCORD_CHANNEL)
            if channel:
                await channel.send(text)

        # VK
        if VK_TOKEN and VK_GROUP_ID:
            vk_url = "https://api.vk.com/method/wall.post"
            params = {
                "owner_id": f"-{VK_GROUP_ID}",
                "from_group": 1,
                "message": text,
                "access_token": VK_TOKEN,
                "v": "5.199",
            }
            r = requests.post(vk_url, params=params)
            print("VK post:", r.text)

        # Telegram
        if TG_TOKEN and TG_CHANNEL:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            payload = {"chat_id": TG_CHANNEL, "text": text, "parse_mode": "HTML"}
            r = requests.post(url, json=payload)
            print("TG post:", r.text)

    except Exception as e:
        await interaction.followup.send(f"Ошибка публикации: {e}", ephemeral=True)

# -------------------- Telegram --------------------
tg_bot = TgBot(TG_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return await message.reply("⛔ Доступ запрещён")
    await message.reply("✅ Бот готов публиковать. Используй команду /news <текст>")

@dp.message(commands=["news"])
async def cmd_news(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return await message.reply("⛔ Доступ запрещён")
    text = message.text.split(" ", 1)
    if len(text) < 2:
        return await message.reply("Укажи текст: /news текст")
    news_text = text[1]

    # постинг в канал
    await tg_bot.send_message(chat_id=TG_CHANNEL, text=news_text)

    # параллельно Discord/VK
    if DISCORD_CHANNEL:
        channel = bot.get_channel(DISCORD_CHANNEL)
        if channel:
            await channel.send(news_text)

    if VK_TOKEN and VK_GROUP_ID:
        vk_url = "https://api.vk.com/method/wall.post"
        params = {
            "owner_id": f"-{VK_GROUP_ID}",
            "from_group": 1,
            "message": news_text,
            "access_token": VK_TOKEN,
            "v": "5.199",
        }
        r = requests.post(vk_url, params=params)
        print("VK post:", r.text)

    await message.reply("📤 Опубликовано")

async def run_telegram():
    await dp.start_polling(tg_bot)

# -------------------- Flask для Render --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# -------------------- Запуск --------------------
if __name__ == "__main__":
    # Запуск Flask в отдельном потоке
    threading.Thread(target=run_flask).start()

    # Telegram (отдельная асинка в потоке)
    threading.Thread(target=lambda: asyncio.run(run_telegram())).start()

    # Discord
    bot.run(DISCORD_TOKEN)
