import discord
from discord.ext import commands
import vk_api
import aiohttp
import asyncio
from aiogram import Bot as TgBot
from aiogram.types import InputFile
import threading
from flask import Flask
import os

# ------------------ Настройки ------------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"

# ------------------ Discord ------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# ------------------ VK ------------------
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# ------------------ Telegram ------------------
tg_bot = TgBot(token=TG_TOKEN)

# ------------------ Flask ------------------
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ------------------ Функции публикации ------------------
async def post_to_services(text, images=None):
    # Discord
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        if images:
            files = [discord.File(img) for img in images[:5]]
            await channel.send(content=text, files=files)
        else:
            await channel.send(content=text)
    # VK
    try:
        attachments = []
        if images:
            upload = vk_api.VkUpload(vk)
            for img_url in images[:5]:
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_url) as resp:
                        data = await resp.read()
                        with open("temp.jpg", "wb") as f:
                            f.write(data)
                        photo = upload.photo_wall("temp.jpg")[0]
                        attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
            os.remove("temp.jpg")
        vk.wall.post(owner_id=-VK_GROUP_ID, message=text, attachments=",".join(attachments))
    except Exception as e:
        print("VK post error:", e)
    # Telegram
    try:
        if images:
            media = [InputFile(img) for img in images[:5]]
            for f in media:
                await tg_bot.send_photo(chat_id=TG_CHANNEL, photo=f, caption=text)
        else:
            await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    except Exception as e:
        print("Telegram post error:", e)

# ------------------ Discord команды ------------------
@bot.command()
async def news(ctx, *, text):
    await post_to_services(text)
    await ctx.send("✅")

@bot.command()
async def text(ctx, *, text):
    channel = bot.get_channel(DISCORD_CHANNEL)
    if channel:
        await channel.send(text)
    await ctx.send("✅")

# ------------------ Запуск ------------------
if __name__ == "__main__":
    # Flask
    threading.Thread(target=run_flask, daemon=True).start()
    # Discord
    bot.run(DISCORD_TOKEN)
