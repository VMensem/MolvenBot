# bot.py
import os, asyncio, threading, logging, requests
import discord
from discord import Intents
from discord.ext import commands
import vk_api

# ---- Telegram (aiogram 3.x) ----
from aiogram import Bot as TgBot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

from flask import Flask

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
        await bot.tree.sync()
    except Exception as e:
        print(f"Sync error: {e}")

@bot.tree.command(name="ping", description="Проверка бота")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!", ephemeral=True)

@bot.tree.command(name="news", description="Опубликовать новость (до 5 фото через пробел)")
async def news(interaction: discord.Interaction, text: str):
    await interaction.response.defer()
    await publish_everywhere(text)
    await interaction.followup.send("✅")

# ---------- Telegram ----------
tg_bot = TgBot(TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def tg_start(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    await message.answer("Привет! Отправь /news <текст> [url1 url2 ...] (до 5 фото)")

@dp.message(Command("news"))
async def tg_news(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Напиши текст после /news")
        return
    # текст до первого http
    text_parts, photo_urls = [], []
    for a in args[1:]:
        if a.lower().startswith("http") and len(photo_urls) < 5:
            photo_urls.append(a)
        else:
            text_parts.append(a)
    text = " ".join(text_parts)
    await publish_everywhere(text, photo_urls)
    await message.answer("✅")

# ---------- Публикация ----------
async def publish_everywhere(text: str, photo_urls=None):
    photo_urls = photo_urls or []

    # Discord
    if DISCORD_CHANNEL:
        channel = bot.get_channel(DISCORD_CHANNEL)
        if channel:
            if photo_urls:
                files = [discord.File(fp=requests.get(u, stream=True).raw, filename=f"img{i}.jpg")
                         for i, u in enumerate(photo_urls)]
                await channel.send(content=text, files=files)
            else:
                await channel.send(text)

    # ВКонтакте
    try:
        vk = vk_api.VkApi(token=VK_TOKEN)
        vk.method("wall.post", {"owner_id": -VK_GROUP_ID, "from_group": 1, "message": text})
    except Exception as e:
        print("VK ошибка:", e)

    # Telegram
    try:
        if photo_urls:
            media = [types.InputMediaPhoto(media=u, caption=text if i == 0 else "")
                     for i, u in enumerate(photo_urls)]
            await tg_bot.send_media_group(chat_id=TG_CHANNEL, media=media)
        else:
            await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    except Exception as e:
        print("TG ошибка:", e)

# ---------- Flask (для ping) ----------
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------- Telegram loop без signal ----------
async def run_telegram():
    # start_polling с handle_signals=False убирает проблему set_wakeup_fd
    await dp.start_polling(tg_bot, handle_signals=False)

# ---------- MAIN ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=lambda: asyncio.run(run_telegram()), daemon=True).start()
    bot.run(DISCORD_TOKEN)
