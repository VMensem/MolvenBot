import os
import threading
import asyncio
import discord
from discord.ext import commands
from flask import Flask
import requests
from aiogram import Bot as TgBot, Dispatcher, types

# -------------------- Конфигурация --------------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"

CREATOR_ID = 1951437901  # ID в Telegram, которому доступны команды

# -------------------- Flask --------------------
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# -------------------- Discord --------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def publish_all(text: str, images: list = None):
    # 1️⃣ Discord
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        files = []
        if images:
            for i, url in enumerate(images[:5]):
                try:
                    r = requests.get(url)
                    r.raise_for_status()
                    files.append(discord.File(fp=io.BytesIO(r.content), filename=f"image{i}.png"))
                except:
                    continue
        await channel.send(content=text, files=files if files else None)

    # 2️⃣ VK
    if VK_TOKEN and VK_GROUP_ID:
        vk_api_url = f"https://api.vk.com/method/wall.post"
        data = {"owner_id": f"-{VK_GROUP_ID}", "message": text, "access_token": VK_TOKEN, "v": "5.131"}
        requests.post(vk_api_url, data=data)

    # 3️⃣ Telegram
    if TG_TOKEN and TG_CHANNEL:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TG_CHANNEL, "text": text})

# Discord команды
@bot.tree.command(name="news", description="Опубликовать новость")
async def news(interaction: discord.Interaction, text: str):
    await publish_all(text)
    await interaction.response.send_message("✅", ephemeral=True)

@bot.tree.command(name="text", description="Отправить текст в Discord канал")
async def text(interaction: discord.Interaction, text: str):
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        await channel.send(text)
        await interaction.response.send_message("✅", ephemeral=True)

# -------------------- Telegram --------------------
tg_bot = TgBot(token=TG_TOKEN)
dp = Dispatcher()

@dp.message()
async def start(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    if message.text.startswith("/start"):
        await message.reply("Привет! Используй /news чтобы отправить новость.")

@dp.message()
async def telegram_news(message: types.Message):
    if message.from_user.id != CREATOR_ID:
        return
    if message.text.startswith("/news"):
        text = message.text.replace("/news", "").strip()
        if text:
            await publish_all(text)
            await message.reply("✅")

# -------------------- Запуск --------------------
async def main():
    tg_task = asyncio.create_task(dp.start_polling(tg_bot, skip_updates=True))
    discord_task = asyncio.create_task(bot.start(DISCORD_TOKEN))
    await asyncio.gather(tg_task, discord_task)

if __name__ == "__main__":
    import io
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
