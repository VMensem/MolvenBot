# --------- Настройки ---------
DISCORD_TOKEN   = "MTQxMzYwNzM0Mjc3NTQ2ODE3NA.G9B618.UQaioB7Awaq4okHNxwEPDBb8lNKu5k5p2NglVk"
DISCORD_CHANNEL = 1413563583966613588

VK_TOKEN        = "vk1.a.5R6wTw5b0WL79JtWYJgYsgQVqrgzS27dLpQqjs40UauxEBq-hEFTeMylKLmwhlbuiJOZ183qe-d-pEIyNpo4s235x_TwmVdGjYgTkw2MO3NBGR-jKbTS4dh73Ny1nisTePTMW7FM2UCtEQaDet0YA-7dXqSP6zKDldrw7AzBmqT_oK0HK99RYrqmvAJkn9JBO3c4qmBILx_e1udBfWM52w"
VK_GROUP_ID     = 219539602

TG_TOKEN        = "8462639289:AAGKFtkNIEzdd_-48_MjelPcdr97GJgtGno"
TG_CHANNEL      = "@MolvenRP"
CREATOR_ID      = 1951437901

# bot.py
import asyncio
import os

# ---------- Discord ----------
import discord
from discord import app_commands

# ---------- Telegram ----------
from aiogram import Bot as TgBot, Dispatcher, types
from aiogram.filters import Command

# ===== Discord setup =====
intents = discord.Intents.default()
intents.message_content = True  # чтобы работали команды на текст

class DiscordClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Регистрируем слэш-команды
        @self.tree.command(name="news", description="Отправить новость в чат")
        async def news_cmd(interaction: discord.Interaction, text: str):
            await interaction.response.send_message(f"Новость: {text}", ephemeral=True)

        @self.tree.command(name="text", description="Отправить текст в чат")
        async def text_cmd(interaction: discord.Interaction, text: str):
            await interaction.response.send_message(f"Текст: {text}", ephemeral=True)

        await self.tree.sync()

discord_client = DiscordClient()

# ===== Telegram setup =====
tg_bot = TgBot(token=TELEGRAM_TOKEN, parse_mode="HTML")
dp = Dispatcher()

async def set_tg_commands():
    await tg_bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="news", description="Отправить новость в канал"),
        types.BotCommand(command="text", description="Отправить текст в канал"),
    ])

def only_owner(handler):
    async def wrapper(message: types.Message):
        if message.from_user.id != CREATOR_ID:
            return await message.answer("⛔ Доступ запрещён")
        return await handler(message)
    return wrapper

@dp.message(Command("start"))
@only_owner
async def start_cmd(m: types.Message):
    await m.answer("Бот готов. Доступны /news и /text")

@dp.message(Command("news"))
@only_owner
async def news_cmd(m: types.Message):
    text = m.get_args()
    if not text:
        return await m.answer("Укажи текст после /news")
    await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    await m.answer("✅ Новость отправлена в канал")

@dp.message(Command("text"))
@only_owner
async def text_cmd(m: types.Message):
    text = m.get_args()
    if not text:
        return await m.answer("Укажи текст после /text")
    await tg_bot.send_message(chat_id=TG_CHANNEL, text=text)
    await m.answer("✅ Текст отправлен в канал")

# ===== Unified runner =====
async def main():
    # Telegram: сразу выставляем команды
    await set_tg_commands()

    # Запускаем Discord и Telegram вместе
    await asyncio.gather(
        discord_client.start(DISCORD_TOKEN),
        dp.start_polling(tg_bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
