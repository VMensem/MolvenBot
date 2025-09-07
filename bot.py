import discord
from discord.ext import commands
from flask import Flask
import threading, os, tempfile, requests
import vk_api
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from typing import List, Optional

# --------- НАСТРОЙКИ (твоё) ---------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588   # id канала Discord

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602  # id группы ВКонтакте (без минуса)

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"  # username канала Telegram (с @)

# --------- ИНИЦИАЛИЗАЦИЯ ---------
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

tg_bot = Bot(token=TG_TOKEN)

# --------- ХЕЛПЕР ДЛЯ VK ---------
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

# --------- ХЕЛПЕР ДЛЯ TELEGRAM ---------
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

# --------- /news для Discord ---------
@bot.tree.command(name="news", description="Опубликовать новость в Discord + VK + Telegram")
@discord.app_commands.describe(
    text="Текст новости",
    images="Прикреплённые файлы (jpg/png), до 5"
)
async def news(interaction: discord.Interaction, text: str, images: Optional[List[discord.Attachment]] = None):
    await interaction.response.defer()

    files = []
    vk_attachments = []

    if images:
        if len(images) > 5:
            await interaction.followup.send("Можно прикрепить максимум 5 изображений.", ephemeral=True)
            return
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

# --------- /text для Discord ---------
@bot.tree.command(name="text", description="Отправить обычный текст в чат")
@discord.app_commands.describe(content="Текст сообщения")
async def text_command(interaction: discord.Interaction, content: str):
    await interaction.response.send_message(content)
    send_to_telegram(content)  # отправка в Telegram

# --------- /help для Discord ---------
@bot.tree.command(name="help", description="Список команд бота")
async def help_cmd(interaction: discord.Interaction):
    txt = (
        "**/news** – отправить текст и/или до 5 картинок в Discord + VK + Telegram\n"
        "**/text** – отправить обычный текст в чат\n"
        "**/help** – показать эту справку"
    )
    await interaction.response.send_message(txt, ephemeral=True)
    send_to_telegram(txt)

# --------- Telegram команды ---------
async def tg_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) or "Текст новости"
    send_to_telegram(text)
    await update.message.reply_text("Новость отправлена ✅")

async def tg_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) or "Текст"
    send_to_telegram(text)
    await update.message.reply_text("Текст отправлен ✅")

async def tg_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "/news – отправить текст новости\n"
        "/text – отправить текст\n"
        "/help – показать справку"
    )
    send_to_telegram(txt)
    await update.message.reply_text(txt)

tg_app = ApplicationBuilder().token(TG_TOKEN).build()
tg_app.add_handler(CommandHandler("news", tg_news))
tg_app.add_handler(CommandHandler("text", tg_text))
tg_app.add_handler(CommandHandler("help", tg_help))

def run_telegram():
    tg_app.run_polling()

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
    threading.Thread(target=run_flask).start()     # Flask
    threading.Thread(target=run_telegram).start()  # Telegram
    bot.run(DISCORD_TOKEN)                         # Discord
