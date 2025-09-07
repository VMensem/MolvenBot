import os
import asyncio
import discord
from discord.ext import commands
import vk_api
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from flask import Flask
import threading

# ------------------- Токены и настройки -------------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"
CREATOR_ID      = 1951437901  # Только ты

# ------------------- Discord -------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ------------------- VK -------------------
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

async def send_to_vk(text, attachments=[]):
    upload = vk_api.VkUpload(vk_session)
    photos = []
    for att in attachments[:5]:
        if att.startswith("http"):
            async with aiohttp.ClientSession() as session:
                async with session.get(att) as resp:
                    data = await resp.read()
            with open("temp.jpg", "wb") as f:
                f.write(data)
            photo = upload.photo_wall("temp.jpg")[0]
        else:
            photo = upload.photo_wall(att)[0]
        photos.append(f"photo{photo['owner_id']}_{photo['id']}")
    vk.wall.post(owner_id=-VK_GROUP_ID, message=text, attachments=",".join(photos))

# ------------------- Telegram -------------------
tg_bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

async def send_to_telegram(text, attachments=[]):
    media = []
    for att in attachments[:5]:
        if att.startswith("http"):
            media.append(types.InputMediaPhoto(media=att))
    if media:
        await tg_bot.send_media_group(chat_id=TG_CHANNEL, media=media)
    else:
        await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)

# ------------------- Discord команды -------------------
@bot.tree.command(name="news", description="Опубликовать новость")
async def news(interaction: discord.Interaction, text: str, images: list[str] = []):
    await interaction.response.send_message("✅")  # Просто галочка
    # Отправка в Discord
    channel = bot.get_channel(DISCORD_CHANNEL)
    if images:
        files = []
        for url in images[:5]:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.read()
            with open("temp.jpg", "wb") as f:
                f.write(data)
            files.append(discord.File("temp.jpg"))
        await channel.send(content=text, files=files)
    else:
        await channel.send(content=text)
    # VK
    await send_to_vk(text, images)
    # Telegram
    await send_to_telegram(text, images)

@bot.tree.command(name="text", description="Отправить текст только в Discord")
async def text(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("✅")
    channel = bot.get_channel(DISCORD_CHANNEL)
    await channel.send(content=text)

# ------------------- Telegram команды -------------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != CREATOR_ID:
        return
    await message.answer("Бот готов к публикации новостей!")

@dp.message(Command("news"))
async def cmd_news(message: Message):
    if message.from_user.id != CREATOR_ID:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Нужно указать текст новости!")
        return
    text = args[1]
    await message.reply("✅")
    # Публикация в Discord
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        await channel.send(content=text)
    # VK
    await send_to_vk(text)
    # Telegram
    await send_to_telegram(text)

# ------------------- Flask -------------------
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# ------------------- Запуск -------------------
async def main():
    # Запускаем Telegram polling
    await dp.start_polling(tg_bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    # Запуск Discord
    bot.loop.create_task(main())
    bot.run(DISCORD_TOKEN)
