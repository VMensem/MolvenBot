import discord
from discord.ext import commands
import vk_api
from vk_api import VkUpload
import asyncio
import aiohttp
from aiogram import Bot as TgBot, Dispatcher
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
import threading
import os
from flask import Flask

# ----------------- Токены и ID -----------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"
CREATOR_ID      = 1951437901  # Только этот пользователь может писать команды в телеграм

# ----------------- Discord -----------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ----------------- VK -----------------
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
upload = VkUpload(vk_session)

def post_vk(text, photos=[]):
    attachments = []
    for photo_url in photos:
        # Загружаем фото по ссылке
        try:
            response = aiohttp.ClientSession().get(photo_url)
        except:
            continue
        # VK expects local files, так что для простоты можно не использовать фото
    vk.wall.post(owner_id=-VK_GROUP_ID, message=text, attachments=attachments)

# ----------------- Telegram -----------------
tg_bot = TgBot(token=TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(tg_bot)

async def send_telegram(text):
    try:
        await tg_bot.send_message(TG_CHANNEL, text)
    except Exception as e:
        print("TG ERROR:", e)

# ----------------- Flask -----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ----------------- Команды Discord -----------------
@bot.tree.command(name="news", description="Опубликовать новость в Discord + VK + Telegram")
async def news(interaction: discord.Interaction, text: str):
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        await channel.send(text)
    # VK
    post_vk(text)
    # TG
    await send_telegram(text)
    await interaction.response.send_message("✅", ephemeral=True)

@bot.tree.command(name="text", description="Отправить текст в Discord канал")
async def text(interaction: discord.Interaction, text: str):
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        await channel.send(text)
    await interaction.response.send_message("✅", ephemeral=True)

# ----------------- Команды Telegram -----------------
@dp.message(commands=["start", "news"])
async def cmd_start(message: Message):
    if message.from_user.id != CREATOR_ID:
        return
    await message.answer("Бот активен!")

@dp.message(commands=["news"])
async def cmd_news(message: Message):
    if message.from_user.id != CREATOR_ID:
        return
    text = message.text.replace("/news", "").strip()
    if text:
        # Отправка в Discord
        channel = bot.get_channel(DISCORD_CHANNEL)
        if channel:
            await channel.send(text)
        # VK
        post_vk(text)
        # TG
        await send_telegram(text)
        await message.answer("✅")

# ----------------- Запуск -----------------
if __name__ == "__main__":
    # Flask
    threading.Thread(target=run_flask, daemon=True).start()
    # Telegram
    threading.Thread(target=lambda: asyncio.run(dp.start_polling(tg_bot, handle_signals=False)), daemon=True).start()
    # Discord
    bot.run(DISCORD_TOKEN)
