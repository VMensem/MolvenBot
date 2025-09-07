import discord
from discord.ext import commands
from flask import Flask
import threading, os, tempfile, requests
import vk_api

# --------- НАСТРОЙКИ ---------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"          # вставь свой НОВЫЙ токен
DISCORD_CHANNEL = 1413563583966613588   # id канала (можно None)
VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602  # id группы ВКонтакте (без минуса)

# --------- ИНИЦИАЛИЗАЦИЯ ---------
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()

# --------- ХЕЛПЕР ДЛЯ ФОТО ВК ---------
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

# --------- СОБЫТИЕ ON_READY ---------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} готов! Slash-команды синхронизированы.")

# --------- /news с несколькими фото ----------
@bot.tree.command(name="news", description="Опубликовать новость в Discord + ВКонтакте")
@discord.app_commands.describe(
    text="Текст новости",
    images="Прикреплённые файлы (jpg/png), до 5"
)
async def news(interaction: discord.Interaction, text: str, images: discord.Option(list[discord.Attachment], default=None)):
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
                files.append(discord.File(fp, filename=image.filename))
                vk_photo = upload_photo_to_vk(fp)
                if vk_photo:
                    vk_attachments.append(vk_photo)
                os.remove(fp)

    # Discord — обычное сообщение с файлами
    channel = bot.get_channel(DISCORD_CHANNEL) or interaction.channel
    await channel.send(text, files=files)

    # VK — текст + прикрепленные фото
    try:
        vk.wall.post(
            owner_id=f"-{VK_GROUP_ID}",
            message=text,
            attachments=",".join(vk_attachments) if vk_attachments else None
        )
    except Exception as e:
        print("Ошибка публикации в VK:", e)

    await interaction.followup.send("Новость отправлена ✅", ephemeral=True)

# --------- /text ----------
@bot.tree.command(name="text", description="Отправить обычный текст в чат")
@discord.app_commands.describe(content="Текст сообщения")
async def text_command(interaction: discord.Interaction, content: str):
    await interaction.response.send_message(content)

# --------- /help ----------
@bot.tree.command(name="help", description="Список команд бота")
async def help_cmd(interaction: discord.Interaction):
    txt = (
        "**/news** – отправить текст и/или до 5 картинок в Discord + VK\n"
        "**/text** – отправить обычный текст в чат\n"
        "**/help** – показать эту справку"
    )
    await interaction.response.send_message(txt, ephemeral=True)

# --------- Flask для Render ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# --------- Запуск ----------
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()  # Flask в отдельном потоке
    bot.run(DISCORD_TOKEN)                      # Discord-бот
