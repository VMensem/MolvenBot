import asyncio
import threading
import discord
from discord.ext import commands
import vk_api
from vk_api import VkUpload
from aiogram import Bot as TgBot, Dispatcher, types
from aiogram.types import InputFile
from flask import Flask
import aiohttp

# ----------------- Токены и ID -----------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588  # Discord channel ID

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"

CREATOR_ID      = 1951437901  # Только твои команды

# ----------------- Discord Bot -----------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ----------------- VK Bot -----------------
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
vk_upload = VkUpload(vk_session)

# ----------------- Telegram Bot -----------------
tg_bot = TgBot(token=TG_TOKEN)
dp = Dispatcher()

# ----------------- Flask -----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# ----------------- Общая функция публикации -----------------
async def publish_all(text, images_urls):
    # --- Discord ---
    channel = bot.get_channel(DISCORD_CHANNEL)
    files = []
    for url in images_urls[:5]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    files.append(discord.File(fp=bytes(data), filename=url.split("/")[-1]))
    if files:
        await channel.send(content=text, files=files)
    else:
        await channel.send(content=text)
    
    # --- VK ---
    attachments = []
    for url in images_urls[:5]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()
        with open("temp.jpg", "wb") as f:
            f.write(data)
        photo = vk_upload.photo_wall(photos="temp.jpg", group_id=VK_GROUP_ID)[0]
        attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
    vk.wall.post(owner_id=-VK_GROUP_ID, message=text, attachments=",".join(attachments))
    
    # --- Telegram ---
    # Отправляем только если это CREATOR
    await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    for url in images_urls[:5]:
        await tg_bot.send_photo(chat_id=TG_CHANNEL, photo=url)

# ----------------- Discord Commands -----------------
@bot.tree.command(name="news", description="Опубликовать новость")
async def news(interaction: discord.Interaction, text: str, images: str = ""):
    images_list = [i.strip() for i in images.split(",") if i.strip()]
    await publish_all(text, images_list)
    await interaction.response.send_message("✅", ephemeral=True)

@bot.tree.command(name="text", description="Отправить текст только в Discord")
async def text_cmd(interaction: discord.Interaction, text: str, images: str = ""):
    images_list = [i.strip() for i in images.split(",") if i.strip()]
    # Discord только
    channel = bot.get_channel(DISCORD_CHANNEL)
    files = []
    for url in images_list[:5]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()
                files.append(discord.File(fp=bytes(data), filename=url.split("/")[-1]))
    if files:
        await channel.send(content=text, files=files)
    else:
        await channel.send(content=text)
    await interaction.response.send_message("✅", ephemeral=True)

# ----------------- Telegram Handlers -----------------
@dp.message()
async def tg_handler(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    if message.text.startswith("/start"):
        await message.reply("Привет! Используй /news для публикации.")
    elif message.text.startswith("/news"):
        parts = message.text.split("\n")
        text = parts[0].replace("/news", "").strip()
        images = parts[1:] if len(parts) > 1 else []
        await publish_all(text, images)
        await message.reply("✅")

# ----------------- Запуск -----------------
if __name__ == "__main__":
    # Flask
    threading.Thread(target=run_flask).start()
    # Telegram
    threading.Thread(target=lambda: asyncio.run(dp.start_polling(tg_bot, skip_updates=True)), daemon=True).start()
    # Discord
    bot.run(DISCORD_TOKEN)
