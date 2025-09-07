import discord
from discord import app_commands
from discord.ext import commands
import requests
import aiohttp
import asyncio
import os
import threading
from aiogram import Bot as TgBot, Dispatcher
from aiogram.types import Message, ParseMode
from aiogram.client.bot import DefaultBotProperties

# ---------------- Конфигурация ----------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"
CREATOR_ID      = 1951437901  # твой Telegram ID

# ---------------- Discord ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Discord запущен: {bot.user}")
    try:
        await bot.tree.sync()
        print("Команды Discord синхронизированы")
    except Exception as e:
        print(f"Ошибка синхронизации Discord команд: {e}")

async def send_to_discord(text: str, images: list = None):
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        files = []
        if images:
            for img_url in images[:5]:
                response = requests.get(img_url)
                filename = img_url.split("/")[-1]
                files.append(discord.File(fp=io.BytesIO(response.content), filename=filename))
        await channel.send(content=text, files=files)

# ---------------- VK ----------------
import vk_api

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

def send_to_vk(text: str, images: list = None):
    attachments = []
    if images:
        upload = vk_api.VkUpload(vk)
        for img_url in images[:5]:
            response = requests.get(img_url)
            with open("temp.jpg", "wb") as f:
                f.write(response.content)
            photo = upload.photo_wall("temp.jpg", group_id=VK_GROUP_ID)[0]
            attachments.append(f'photo{photo["owner_id"]}_{photo["id"]}')
            os.remove("temp.jpg")
    vk.wall.post(owner_id=-VK_GROUP_ID, message=text, attachments=",".join(attachments))

# ---------------- Telegram ----------------
tg_bot = TgBot(
    TG_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML, request_timeout=60)
)
dp = Dispatcher()

async def send_to_telegram(text: str, images: list = None):
    media = []
    if images:
        for img_url in images[:5]:
            media.append({"type":"photo","media":img_url})
    if media:
        await tg_bot.send_media_group(TG_CHANNEL, media)
    else:
        await tg_bot.send_message(TG_CHANNEL, text)

@dp.message(commands=["start"])
async def start_cmd(message: Message):
    if message.from_user.id != CREATOR_ID:
        return
    await message.answer("Привет! Ты можешь отправлять новости через /news")

# ---------------- Commands ----------------
@bot.tree.command(name="news", description="Опубликовать новость в Discord + VK + Telegram")
@app_commands.describe(text="Текст новости", images="Ссылки на фото через пробел")
)
async def news(interaction: discord.Interaction, text: str, images: str = None):
    await interaction.response.defer()
    imgs = images.split() if images else []
    await send_to_discord(text, imgs)
    send_to_vk(text, imgs)
    await send_to_telegram(text, imgs)
    await interaction.followup.send("✅", ephemeral=True)

@bot.tree.command(name="text", description="Отправить текст только в Discord")
@app_commands.describe(text="Текст для Discord", images="Ссылки на фото через пробел")
)
async def text(interaction: discord.Interaction, text: str, images: str = None):
    await interaction.response.defer()
    imgs = images.split() if images else []
    await send_to_discord(text, imgs)
    await interaction.followup.send("✅", ephemeral=True)

# ---------------- Flask ----------------
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ---------------- Запуск ----------------
if __name__ == "__main__":
    import io
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(dp.start_polling(tg_bot, handle_signals=False)), daemon=True).start()
    bot.run(DISCORD_TOKEN)
