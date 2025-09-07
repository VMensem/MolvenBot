import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import aiohttp
import vk_api

# ---------------- CONFIG ----------------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"          # вставь свой НОВЫЙ токен
DISCORD_CHANNEL = 1413563583966613588   # id канала (можно None)

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602  # id группы ВКонтакте (без минуса)

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"          # токен бота Telegram
TG_CHANNEL      = "@MolvenRP"             # username канала Telegram (с @)
# ----------------------------------------

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Helper Functions ----------
async def post_to_telegram(text: str):
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            payload = {"chat_id": TG_CHANNEL, "text": text}
            async with session.post(url, data=payload, timeout=10) as resp:
                if resp.status != 200:
                    print(f"[TG ERROR] Status: {resp.status}")
    except Exception as e:
        print(f"[TG ERROR] {e}")

def post_to_vk(text: str, images: List[str] = []):
    try:
        vk = vk_api.VkApi(token=VK_TOKEN)
        upload = vk_api.VkUpload(vk)
        photo_ids = []

        for img_url in images:
            try:
                # Загружаем фото по ссылке
                photo = upload.photo_wall(img_url)
                if photo and 'id' in photo[0]:
                    photo_ids.append(f"photo{photo[0]['owner_id']}_{photo[0]['id']}")
            except Exception as e:
                print(f"[VK IMAGE ERROR] {e}")

        attachments = ",".join(photo_ids) if photo_ids else None
        vk.method("wall.post", {
            "owner_id": -VK_GROUP_ID,
            "message": text,
            "attachments": attachments
        })
    except Exception as e:
        print(f"[VK ERROR] {e}")

async def post_to_discord(text: str, images: List[str] = []):
    try:
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        if not channel:
            print("[DS ERROR] Channel not found")
            return

        # Отправляем текст с изображениями по ссылке
        content = text
        for img_url in images:
            content += f"\n{img_url}"
        await channel.send(content=content)
    except Exception as e:
        print(f"[DS ERROR] {e}")

async def post_to_services(text: str, images: List[str] = []):
    await post_to_discord(text, images)
    await post_to_telegram(text)
    post_to_vk(text, images)

# ---------- Discord Commands ----------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="news", description="Опубликовать новость")
@app_commands.describe(text="Текст новости", image1="Ссылка на изображение 1 (необязательно)",
                       image2="Ссылка на изображение 2 (необязательно)", image3="Ссылка на изображение 3",
                       image4="Ссылка на изображение 4", image5="Ссылка на изображение 5")
async def news(interaction: discord.Interaction,
               text: str,
               image1: Optional[str] = None,
               image2: Optional[str] = None,
               image3: Optional[str] = None,
               image4: Optional[str] = None,
               image5: Optional[str] = None):
    await interaction.response.send_message("✅", ephemeral=True)
    images = [img for img in [image1, image2, image3, image4, image5] if img]
    await post_to_services(text, images)

@bot.tree.command(name="text", description="Отправить текст в Discord")
@app_commands.describe(text="Текст для отправки")
async def text(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("✅", ephemeral=True)
    await post_to_discord(text)

# ---------- Run Bot ----------
bot.run(DISCORD_TOKEN)
