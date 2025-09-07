# bot.py
import os, asyncio, threading, logging, requests
import discord
from discord import Intents
from discord.ext import commands
import vk_api

from aiogram import Bot as TgBot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

from flask import Flask
from io import BytesIO

# ---------- НАСТРОЙКИ ----------
DISCORD_TOKEN   = "<DISCORD_TOKEN>"
DISCORD_CHANNEL = 123456789012345678

VK_TOKEN        = "<VK_TOKEN>"
VK_GROUP_ID     = 123456789

TG_TOKEN        = "<TG_TOKEN>"
TG_CHANNEL      = "@yourchannel"
CREATOR_ID      = 1951437901

# ---------- Discord ----------
intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Discord: {bot.user} запущен")
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"Sync error: {e}")

@bot.tree.command(name="ping", description="Проверка бота")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)

@bot.tree.command(name="news", description="Опубликовать новость (до 5 фото через пробел)")
async def news(interaction: discord.Interaction, text: str):
    await interaction.response.defer()
    photo_urls = [att.url for att in getattr(interaction, "attachments", [])][:5]
    await publish_everywhere(text, photo_urls)
    await interaction.followup.send("✅")

@bot.tree.command(name="text", description="Отправить текст в Discord канал (до 5 фото)")
async def text(interaction: discord.Interaction, text: str):
    await interaction.response.defer()
    photo_urls = [att.url for att in getattr(interaction, "attachments", [])][:5]

    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        files = []
        for u in photo_urls:
            if isinstance(u, str):
                files.append(discord.File(fp=BytesIO(requests.get(u).content),
                                          filename=f"img{len(files)}.jpg"))
            else:
                files.append(discord.File(fp=u, filename=f"img{len(files)}.jpg"))
        if files:
            await channel.send(content=text, files=files)
        else:
            await channel.send(text)
    await interaction.followup.send("✅")

# ---------- Telegram ----------
tg_bot = TgBot(TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def tg_start(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    await message.answer("Привет! Отправь /news <текст> [ссылки] или прикрепи фото (до 5)")

@dp.message(Command("news"))
async def tg_news(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    args = message.text.split()
    if len(args) < 2 and not message.photo:
        await message.answer("Напиши текст после /news или прикрепи фото")
        return
    # текст и ссылки
    text_parts, photo_urls = [], []
    for a in args[1:]:
        if a.lower().startswith("http") and len(photo_urls) < 5:
            photo_urls.append(a)
        else:
            text_parts.append(a)
    text = " ".join(text_parts)

    # проверяем вложения
    if message.photo:
        for p in message.photo[:5]:
            file = await tg_bot.download_file_by_id(p.file_id)
            bio = BytesIO(file.read())
            bio.name = f"{p.file_id}.jpg"
            photo_urls.append(bio)

    await publish_everywhere(text, photo_urls)
    await message.answer("✅")

# ---------- Публикация ----------
async def publish_everywhere(text: str, photo_urls=None):
    photo_urls = photo_urls or []

    # Discord
    if DISCORD_CHANNEL:
        channel = bot.get_channel(DISCORD_CHANNEL)
        if channel:
            files = []
            for u in photo_urls[:5]:
                if isinstance(u, str):
                    files.append(discord.File(fp=BytesIO(requests.get(u).content),
                                              filename=f"img{len(files)}.jpg"))
                else:
                    files.append(discord.File(fp=u, filename=f"img{len(files)}.jpg"))
            if files:
                await channel.send(content=text, files=files)
            else:
                await channel.send(text)

    # VK
    try:
        vk = vk_api.VkApi(token=VK_TOKEN)
        attachments = []
        for u in photo_urls[:5]:
            if isinstance(u, str):
                content = requests.get(u).content
            else:
                content = u.read()
            upload = vk.method("photos.getWallUploadServer", {"group_id": VK_GROUP_ID})
            files = {"photo": ("img.jpg", content)}
            r = requests.post(upload["upload_url"], files=files).json()
            photo = vk.method("photos.saveWallPhoto", {"group_id": VK_GROUP_ID,
                                                       "photo": r["photo"],
                                                       "server": r["server"],
                                                       "hash": r["hash"]})
            attachments.append(f'photo{photo[0]["owner_id"]}_{photo[0]["id"]}')
        vk.method("wall.post", {"owner_id": -VK_GROUP_ID, "from_group": 1, "message": text,
                                "attachments": ",".join(attachments)})
    except Exception as e:
        print("VK ошибка:", e)

    # Telegram
    try:
        media = []
        for i, u in enumerate(photo_urls[:5]):
            if isinstance(u, str):
                media.append(types.InputMediaPhoto(media=u, caption=text if i == 0 else ""))
            else:
                media.append(types.InputMediaPhoto(media=u, caption=text if i == 0 else ""))
        if media:
            await tg_bot.send_media_group(chat_id=TG_CHANNEL, media=media)
        else:
            await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    except Exception as e:
        print("TG ошибка:", e)

# ---------- Flask ----------
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------- Telegram loop без signal ----------
async def run_telegram():
    await dp.start_polling(tg_bot, handle_signals=False)

# ---------- MAIN ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(run_telegram()), daemon=True).start()
    bot.run(DISCORD_TOKEN)
