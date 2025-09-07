import asyncio
import aiohttp
import discord
from discord.ext import commands
import vk_api
from vk_api import VkUpload
import threading

# ===================== Настройки =====================
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHAT_ID      = -1003091449025  # твой чат в Telegram

# ===================== Discord =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== VK =====================
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
vk_upload = VkUpload(vk_session)

# ===================== Telegram =====================
from aiogram import Bot, Dispatcher
tg_bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

# ===================== Функция публикации =====================
async def post_to_services(text, image_urls=None):
    # ---------- Telegram ----------
    try:
        media = []
        if image_urls:
            for url in image_urls:
                try:
                    media.append(await tg_bot.send_photo(chat_id=TG_CHAT_ID, photo=url))
                except Exception as e:
                    print(f"TG photo error: {e}")
        await tg_bot.send_message(chat_id=TG_CHAT_ID, text=text)
    except Exception as e:
        print(f"TG error: {e}")

    # ---------- Discord ----------
    try:
        channel = bot.get_channel(DISCORD_CHANNEL)
        if channel:
            if image_urls:
                files = []
                for url in image_urls:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                data = await resp.read()
                                files.append(discord.File(fp=io.BytesIO(data), filename="image.jpg"))
                await channel.send(content=text, files=files)
            else:
                await channel.send(text)
    except Exception as e:
        print(f"Discord error: {e}")

    # ---------- VK ----------
    try:
        attachments = []
        if image_urls:
            for url in image_urls:
                try:
                    photo = vk_upload.photo_wall(photos=url, group_id=VK_GROUP_ID)
                    attachments.append(f'photo{photo[0]["owner_id"]}_{photo[0]["id"]}')
                except Exception as e:
                    print(f"VK photo error: {e}")
        vk.wall.post(owner_id=-VK_GROUP_ID, message=text, attachments=",".join(attachments) if attachments else None)
    except Exception as e:
        print(f"VK error: {e}")

# ===================== Команда для Discord =====================
@bot.tree.command(name="news", description="Опубликовать новость")
async def news(interaction: discord.Interaction, text: str, image_urls: str = None):
    image_list = image_urls.split(",") if image_urls else None
    await post_to_services(text, image_list)
    await interaction.response.send_message("✅", ephemeral=True)

# ===================== Запуск Telegram в фоне =====================
def start_telegram():
    asyncio.run(dp.start_polling(tg_bot, skip_updates=True))

threading.Thread(target=start_telegram, daemon=True).start()

# ===================== Запуск Discord =====================
bot.run(DISCORD_TOKEN)
