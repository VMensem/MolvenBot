
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

# bot.py
"""
Molven Project — публикация новости в Discord, Telegram и VK
Discord slash-команды:
  /news <текст> — публикация во все сервисы
  /text <текст> — сообщение только в канал Discord
"""

import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands
from aiogram import Bot as TgBot
import vk_api

# -----------------------------------------------------------
# НАСТРОЙКИ
# -----------------------------------------------------------

DISCORD_TOKEN = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
GUILD_ID = 123456789012345678        # ID твоего сервера

TG_TOKEN = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHAT_ID = -1003091449025               # чат/канал для новостей

VK_TOKEN = "vk1.a.LZnqNzchEADk_n27uAHk6PlqhY0kDuvjBV3T321R-iBahhcKyvZ2-G4QgdNv62bI9WwgZxNSYzbc17kkNaUdbGAA6Q4Alpn1gxo8ZQitMotmFMEKZFB9Wcy_e0IhDIZJN6p3pFBBSPr7SmZ5SuFgPvkM0jLRVoSG3uEfBTUAk-HU4uAGoYM7nbgyjNrLOHpUkVGM5S6N6wSEvYd2TEDhvQ"
VK_GROUP_ID = 209873316                    # id группы (без минуса)

# -----------------------------------------------------------
# ЛОГИ
# -----------------------------------------------------------

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("molven")

# -----------------------------------------------------------
# КЛИЕНТЫ
# -----------------------------------------------------------

# Telegram
tg_bot = TgBot(token=TG_TOKEN)

# Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# VK
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()


# -----------------------------------------------------------
# ФУНКЦИЯ ПУБЛИКАЦИИ
# -----------------------------------------------------------

async def post_to_services(text: str):
    # Telegram
    try:
        await tg_bot.send_message(chat_id=TG_CHAT_ID, text=text)
        log.info("Опубликовано в Telegram")
    except Exception as e:
        log.error(f"Ошибка Telegram: {e}")

    # VK
    try:
        vk.wall.post(owner_id=-VK_GROUP_ID, message=text, from_group=1)
        log.info("Опубликовано в VK")
    except Exception as e:
        log.error(f"Ошибка VK: {e}")


# -----------------------------------------------------------
# SLASH-КОМАНДЫ
# -----------------------------------------------------------

@bot.tree.command(name="news", description="Опубликовать новость в TG + VK + Discord")
@app_commands.describe(text="Текст новости")
async def news(interaction: discord.Interaction, text: str):
    await interaction.response.send_message(f"Новость отправлена:\n{text}")
    await post_to_services(text)


@bot.tree.command(name="text", description="Отправить сообщение только в этот канал Discord")
@app_commands.describe(text="Сообщение для Discord")
async def text(interaction: discord.Interaction, text: str):
    # просто дублируем сообщение в канал, где вызвали
    await interaction.response.send_message(text)


# -----------------------------------------------------------
# СТАРТ
# -----------------------------------------------------------

async def main():
    async with tg_bot:
        # синхронизируем команды для конкретного сервера, чтобы появлялись мгновенно
        try:
            guild = discord.Object(id=GUILD_ID)
            await bot.tree.sync(guild=guild)
            log.info("Slash-команды синхронизированы")
        except Exception as e:
            log.error(f"Ошибка синхронизации команд: {e}")
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
