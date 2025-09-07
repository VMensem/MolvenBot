import os
import threading
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

import vk_api
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InputFile
from aiogram.filters import Command

from flask import Flask

# ================== CONFIG ==================
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"
CREATOR_ID      = 1951437901

MAX_IMAGES = 5
# ============================================

# ---------- Discord ----------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ---------- VK ----------
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# ---------- Telegram ----------
tg_bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

# ---------- Flask ----------
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ---------- VK FUNCTIONS ----------
def upload_photos_to_vk(urls):
    attachments = []
    for url in urls[:MAX_IMAGES]:
        response = vk.photos.getWallUploadServer(group_id=VK_GROUP_ID)
        upload_url = response['upload_url']
        # Скачиваем фото временно
        import requests, tempfile
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        r = requests.get(url)
        tmp_file.write(r.content)
        tmp_file.close()
        # Загружаем
        with open(tmp_file.name, "rb") as f:
            import json
            files = {"photo": f}
            import requests
            res = requests.post(upload_url, files=files).json()
        save_res = vk.photos.saveWallPhoto(group_id=VK_GROUP_ID, photo=res['photo'], server=res['server'], hash=res['hash'])
        attachments.append(f"photo{VK_GROUP_ID}_{save_res[0]['id']}")
    return attachments

# ---------- Discord Commands ----------
@bot.tree.command(name="news", description="Опубликовать новость")
@app_commands.describe(text="Текст новости", images="Ссылки на изображения")
async def news(interaction: discord.Interaction, text: str, images: str = ""):
    await interaction.response.defer()
    urls = images.split() if images else []
    channel = bot.get_channel(DISCORD_CHANNEL)
    content = text
    files = []
    for i, url in enumerate(urls[:MAX_IMAGES]):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    import io
                    files.append(discord.File(io.BytesIO(data), f"image{i}.png"))
    if channel:
        await channel.send(content, files=files)
    # VK
    if urls:
        upload_photos_to_vk(urls)
    # Telegram
    if urls:
        media = []
        for url in urls[:MAX_IMAGES]:
            media.append(InputFile.from_url(url))
        await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    else:
        await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    await interaction.followup.send("✅", ephemeral=True)

@bot.tree.command(name="text", description="Отправить текст в Discord")
@app_commands.describe(text="Текст для отправки")
async def text(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(text)

# ---------- Telegram Handlers ----------
@dp.message(Command(commands=["start"]))
async def start(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    await message.answer("Привет! Это бот Molven RolePlay.")

@dp.message(Command(commands=["news"]))
async def telegram_news(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Напиши текст после команды /news")
        return
    text = args[1]
    # Отправка в Discord
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        await channel.send(text)
    # VK
    # Для Telegram поста без фото
    await message.answer("✅")

async def run_telegram():
    await dp.start_polling(tg_bot, handle_signals=False)

# ---------- Main ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(run_telegram()), daemon=True).start()
    bot.run(DISCORD_TOKEN)
