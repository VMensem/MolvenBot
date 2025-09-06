import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
import vk_api, requests, os
import tempfile

# --------- НАСТРОЙКИ ---------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"          # вставь свой НОВЫЙ токен
DISCORD_CHANNEL = 1413563583966613588   # id канала (можно None)
VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602  # id группы ВКонтакте (без минуса)

# --------- ИНИЦИАЛИЗАЦИЯ ---------
intents = discord.Intents.default()
intents.guilds = True
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

# --------- /ping ----------
@bot.tree.command(name="ping", description="Пинг команда")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# --------- /news ----------
@bot.tree.command(name="news", description="Опубликовать новость в Discord + ВКонтакте")
@app_commands.describe(
    text="Текст новости",
    image="Прикреплённый файл (jpg/png)",
    color="Цвет рамки embed в Discord"
)
@app_commands.choices(
    color=[
        app_commands.Choice(name="Красный", value="red"),
        app_commands.Choice(name="Зелёный", value="green"),
        app_commands.Choice(name="Синий", value="blue"),
        app_commands.Choice(name="Золотой", value="gold"),
        app_commands.Choice(name="Случайный", value="random"),
    ]
)
async def news(interaction: discord.Interaction, text: str, image: discord.Attachment = None, color: str = "blue"):
    await interaction.response.defer()
    
    col = getattr(discord.Color, color)() if color != "random" else discord.Color.random()
    embed = discord.Embed(description=text, color=col)
    embed.set_author(name="Molven RolePlay", icon_url=bot.user.avatar.url)

    files = []
    fp = None
    if image:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
            fp = tmp.name
            await image.save(fp)
        embed.set_image(url=f"attachment://{image.filename}")
        files.append(discord.File(fp, filename=image.filename))

    # Discord
    channel = bot.get_channel(DISCORD_CHANNEL) or interaction.channel
    await channel.send(embed=embed, files=files)

    # VK
    attachments = []
    if fp:
        vk_photo = upload_photo_to_vk(fp)
        if vk_photo:
            attachments.append(vk_photo)
        os.remove(fp)

    try:
        vk.wall.post(
            owner_id=f"-{VK_GROUP_ID}",
            message=text,
            attachments=",".join(attachments) if attachments else None
        )
    except Exception as e:
        print("Ошибка публикации в VK:", e)

    await interaction.followup.send("Новость отправлена ✅", ephemeral=True)

# --------- /text ----------
@bot.tree.command(name="text", description="Красиво оформить текст в текущий канал")
@app_commands.describe(content="Текст сообщения", color="Цвет рамки embed")
@app_commands.choices(
    color=[
        app_commands.Choice(name="Красный", value="red"),
        app_commands.Choice(name="Зелёный", value="green"),
        app_commands.Choice(name="Синий", value="blue"),
        app_commands.Choice(name="Золотой", value="gold"),
        app_commands.Choice(name="Случайный", value="random"),
    ]
)
async def text_command(interaction: discord.Interaction, content: str, color: str = "blue"):
    col = getattr(discord.Color, color)() if color != "random" else discord.Color.random()
    embed = discord.Embed(description=content, color=col)
    embed.set_author(name="Molven RolePlay", icon_url=bot.user.avatar.url)
    embed.set_footer(text="Molven RolePlay")
    await interaction.response.send_message(embed=embed)

# --------- /help ----------
@bot.tree.command(name="help", description="Справка по командам")
async def help_cmd(interaction: discord.Interaction):
    txt = (
        "**/news** – текст/картинка → Discord + VK\n"
        "**/text** – красиво оформить embed\n"
        "**/ping** – тестовая команда\n"
        "**/help** – список команд"
    )
    await interaction.response.send_message(txt, ephemeral=True)

# ---------- Flask ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ---------- Запуск ----------
if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask).start()
    # Запускаем бота
    bot.run(DISCORD_TOKEN)
