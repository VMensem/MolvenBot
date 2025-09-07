import discord
from discord.ext import commands
from flask import Flask
import threading, os, tempfile, requests
import vk_api
from typing import Optional

# --------- Настройки ---------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"
CREATOR_ID      = 1951437901

# --------- Discord ---------
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --------- VK ---------
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# --------- Telegram Aiogram ---------
import asyncio
from aiogram import Bot as TgBot, Dispatcher, types
from aiogram.filters import Command

tg_bot = TgBot(token=TG_TOKEN)
dp = Dispatcher()

# --------- VK Helper ---------
def upload_photo_to_vk(fp: str) -> str:
    try:
        server = vk.photos.getWallUploadServer(group_id=VK_GROUP_ID)
        with open(fp, "rb") as f:
            r = requests.post(server['upload_url'], files={"photo": f}).json()
        photo = vk.photos.saveWallPhoto(
            group_id=VK_GROUP_ID,
            photo=r['photo'],
            server=r['server'],
            hash=r['hash']
        )[0]
        return f"photo{photo['owner_id']}_{photo['id']}"
    except Exception as e:
        print("Ошибка загрузки фото в VK:", e)
        return None

# --------- Telegram Helper ---------
def send_to_telegram(text: str, files: list = None):
    try:
        if files:
            for f in files:
                tg_bot.send_photo(chat_id=TG_CHANNEL, photo=open(f, "rb"), caption=text)
        else:
            tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    except Exception as e:
        print("Ошибка публикации в Telegram:", e)

# --------- Discord events ---------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} готов! Slash-команды синхронизированы.")

# --------- Discord Commands ---------
@bot.tree.command(name="news", description="Опубликовать новость в Discord + VK + Telegram")
@discord.app_commands.describe(
    text="Текст новости",
    image1="Первая картинка (опционально)",
    image2="Вторая картинка (опционально)",
    image3="Третья картинка (опционально)",
    image4="Четвёртая картинка (опционально)",
    image5="Пятая картинка (опционально)"
)
async def news(
    interaction: discord.Interaction,
    text: str,
    image1: Optional[discord.Attachment] = None,
    image2: Optional[discord.Attachment] = None,
    image3: Optional[discord.Attachment] = None,
    image4: Optional[discord.Attachment] = None,
    image5: Optional[discord.Attachment] = None
):
    await interaction.response.defer()
    images = [img for img in [image1, image2, image3, image4, image5] if img]
    files = []
    vk_attachments = []

    for image in images:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
            fp = tmp.name
            await image.save(fp)
            files.append(fp)
            vk_photo = upload_photo_to_vk(fp)
            if vk_photo:
                vk_attachments.append(vk_photo)

    # Discord
    channel = bot.get_channel(DISCORD_CHANNEL) or interaction.channel
    discord_files = [discord.File(f, filename=os.path.basename(f)) for f in files]
    await channel.send(text, files=discord_files)

    # VK
    try:
        vk.wall.post(
            owner_id=f"-{VK_GROUP_ID}",
            message=text,
            attachments=",".join(vk_attachments) if vk_attachments else None
        )
    except Exception as e:
        print("Ошибка публикации в VK:", e)

    # Telegram
    send_to_telegram(text, files)

    # Удаляем временные файлы
    for f in files:
        os.remove(f)

    await interaction.followup.send("Новость отправлена ✅", ephemeral=True)

@bot.tree.command(name="text", description="Отправить обычный текст в чат")
@discord.app_commands.describe(content="Текст сообщения")
async def text_command(interaction: discord.Interaction, content: str):
    await interaction.response.send_message(content)
    send_to_telegram(content)

@bot.tree.command(name="help", description="Список команд бота")
async def help_cmd(interaction: discord.Interaction):
    txt = (
        "**/news** – отправить текст и/или до 5 картинок в Discord + VK + Telegram\n"
        "**/text** – отправить обычный текст в чат\n"
        "**/help** – показать эту справку"
    )
    await interaction.response.send_message(txt, ephemeral=True)
    send_to_telegram(txt)

# --------- Telegram Aiogram ---------
def is_creator(user_id: int) -> bool:
    return user_id == CREATOR_ID

@dp.message(Command(commands=["start"]))
async def tg_start(message: types.Message):
    if not is_creator(message.from_user.id):
        return
    await message.answer("👋 Привет! Бот готов к публикации новостей.")

@dp.message(Command(commands=["help"]))
async def tg_help(message: types.Message):
    if not is_creator(message.from_user.id):
        return
    txt = (
        "/start – запуск бота\n"
        "/news <текст> – отправить новость в канал\n"
        "/text <текст> – отправить текст в канал\n"
        "/help – показать справку"
    )
    await message.answer(txt)

@dp.message(Command(commands=["news"]))
async def tg_news(message: types.Message):
    if not is_creator(message.from_user.id):
        return
    args = message.get_args()
    if not args:
        await message.answer("❌ Нужно указать текст новости после команды /news")
        return
    send_to_telegram(args)
    await message.answer("✅ Новость отправлена в канал")

@dp.message(Command(commands=["text"]))
async def tg_text(message: types.Message):
    if not is_creator(message.from_user.id):
        return
    args = message.get_args()
    if not args:
        await message.answer("❌ Нужно указать текст после команды /text")
        return
    send_to_telegram(args)
    await message.answer("✅ Текст отправлен в канал")

async def run_telegram():
    await dp.start_polling(tg_bot)

# --------- Flask для Render ----------
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --------- Запуск всего ---------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()       # Flask
    threading.Thread(target=lambda: asyncio.run(run_telegram())).start()  # Telegram
    bot.run(DISCORD_TOKEN)                            # Discord
