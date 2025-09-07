import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
import vk_api
from aiogram import Bot as TgBot, Dispatcher, types
import threading

# ------------------- Токены -------------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"          # вставь свой НОВЫЙ токен
DISCORD_CHANNEL = 1413563583966613588   # id канала (можно None)

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602  # id группы ВКонтакте (без минуса)

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"          # токен бота Telegram
TG_CHANNEL      = "@MolvenRP"             # username канала Telegram (с @)
CREATOR_ID      = 1951437901            # только этот id может писать комманды в ТГ

# ------------------- Discord -------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------- VK -------------------
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

async def send_to_vk(text, images):
    # Загружаем изображения в VK
    attachments = []
    for url in images:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()
        with open("temp_vk.jpg", "wb") as f:
            f.write(data)
        upload = vk_api.VkUpload(vk)
        photo = upload.photo_wall("temp_vk.jpg", group_id=VK_GROUP_ID)
        attachments.append(f"photo{photo[0]['owner_id']}_{photo[0]['id']}")
    vk.wall.post(owner_id=-VK_GROUP_ID, message=text, attachments=",".join(attachments))

# ------------------- Telegram -------------------
tg_bot = TgBot(token=TG_TOKEN)
dp = Dispatcher()

async def send_to_telegram(text, images):
    media = []
    for url in images:
        media.append(types.InputMediaPhoto(media=url))
    if media:
        await tg_bot.send_media_group(chat_id=TG_CHANNEL, media=media)
    else:
        await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    await message.reply("Бот активен ✅")

# ------------------- Discord команды -------------------
@bot.tree.command(name="news", description="Опубликовать новость")
@app_commands.describe(
    text="Текст новости",
    img1="Ссылка на изображение 1 (опционально)",
    img2="Ссылка на изображение 2 (опционально)",
    img3="Ссылка на изображение 3 (опционально)",
    img4="Ссылка на изображение 4 (опционально)",
    img5="Ссылка на изображение 5 (опционально)"
)
async def news(interaction: discord.Interaction, text: str, img1: str = None, img2: str = None, img3: str = None, img4: str = None, img5: str = None):
    await interaction.response.send_message("✅", ephemeral=True)
    channel = bot.get_channel(DISCORD_CHANNEL)
    images = [img for img in [img1, img2, img3, img4, img5] if img]

    if images:
        files = []
        for url in images:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.read()
            with open("temp.jpg", "wb") as f:
                f.write(data)
            files.append(discord.File("temp.jpg"))
        await channel.send(content=text, files=files)
    else:
        await channel.send(content=text)

    await send_to_vk(text, images)
    await send_to_telegram(text, images)

@bot.tree.command(name="text", description="Отправить текст только в Discord")
async def text(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("✅", ephemeral=True)
    channel = bot.get_channel(DISCORD_CHANNEL)
    await channel.send(content=text)

# ------------------- Flask для Render -------------------
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ------------------- Запуск -------------------
def run_telegram():
    import asyncio
    asyncio.run(dp.start_polling(tg_bot, handle_signals=False))

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=run_telegram, daemon=True).start()
    bot.run(DISCORD_TOKEN)
