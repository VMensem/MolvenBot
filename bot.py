import os
import asyncio
import threading
import discord
from discord import app_commands
from discord.ext import commands
import requests
from aiogram import Bot as TgBot
from aiogram.types import InputFile
import aiohttp

# ---------------- CONFIG ----------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588   # id канала

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602  # id группы ВКонтакте (без минуса)

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"  # username канала Telegram

# ---------------- DISCORD BOT ----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# ---------------- TELEGRAM BOT ----------------
tg_bot = TgBot(token=TG_TOKEN)

# ---------------- HELP FUNCTIONS ----------------
async def post_to_services(text, images: list[str] = []):
    # -------- Discord --------
    discord_channel = bot.get_channel(DISCORD_CHANNEL)
    if discord_channel:
        files = []
        for url in images[:5]:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        files.append(discord.File(fp=io.BytesIO(data), filename=os.path.basename(url)))
        await discord_channel.send(content=text, files=files if files else None)

    # -------- VK --------
    upload_url = f"https://api.vk.com/method/photos.getWallUploadServer?group_id={VK_GROUP_ID}&access_token={VK_TOKEN}&v=5.131"
    resp = requests.get(upload_url).json()
    upload_url = resp["response"]["upload_url"]
    
    vk_files = {}
    for i, img_url in enumerate(images[:5]):
        img_data = requests.get(img_url).content
        vk_files[f'photo{i}'] = ('image.jpg', img_data)
    upload_resp = requests.post(upload_url, files=vk_files).json()
    save_resp = requests.get(f"https://api.vk.com/method/photos.saveWallPhoto?access_token={VK_TOKEN}&group_id={VK_GROUP_ID}&server={upload_resp['server']}&photos_list={upload_resp['photos_list']}&hash={upload_resp['hash']}&v=5.131").json()
    attachments = []
    for photo in save_resp['response']:
        attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
    post_data = {
        "owner_id": -VK_GROUP_ID,
        "attachments": ",".join(attachments),
        "message": text,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    requests.post("https://api.vk.com/method/wall.post", data=post_data)

    # -------- Telegram --------
    try:
        if images:
            media = []
            for url in images[:5]:
                media.append({"type": "photo", "media": url})
            await tg_bot.send_media_group(chat_id=TG_CHANNEL, media=media)
        else:
            await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    except Exception as e:
        print(f"Telegram send error: {e}")

# ---------------- DISCORD COMMANDS ----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@app_commands.command(name="news", description="Опубликовать новость")
@app_commands.describe(text="Текст новости", images="Ссылки на изображения (до 5)")
async def news(interaction: discord.Interaction, text: str, images: str = ""):
    image_list = images.split() if images else []
    await post_to_services(text, image_list)
    await interaction.response.send_message("✅")

@app_commands.command(name="text", description="Отправить текст только в Discord")
@app_commands.describe(text="Текст для Discord")
async def text(interaction: discord.Interaction, text: str):
    discord_channel = bot.get_channel(DISCORD_CHANNEL)
    if discord_channel:
        await discord_channel.send(text)
    await interaction.response.send_message("✅")

bot.tree.add_command(news)
bot.tree.add_command(text)

# ---------------- RUN BOT ----------------
if __name__ == "__main__":
    import io
    import flask
    app = flask.Flask(__name__)
    
    @app.route("/")
    def home():
        return "Bot is running!"
    
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000), daemon=True).start()
    bot.run(DISCORD_TOKEN)
