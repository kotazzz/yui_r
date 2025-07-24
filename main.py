import disnake
from disnake.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise RuntimeError("Environment variable 'TOKEN' is not set. Please set it in your .env file or environment.")

# ID тестового сервера
GUILD_ID = int(os.getenv("GUILD_ID", -1))
if GUILD_ID == -1:
    raise RuntimeError("Environment variable 'GUILD_ID' is not set. Please set it in your .env file or environment.")


intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, test_guilds=[GUILD_ID])

# Загрузка экстеншенов
bot.load_extension("extensions.verification")
bot.load_extension("extensions.admin_roles")

print(bot.extensions)

@bot.slash_command(
    name="meow",
    description="Тестовая команда",
)
async def meow(inter: disnake.ApplicationCommandInteraction):
    print(type(inter))
    await inter.response.send_message("Привет! Я базовый disnake бот.")

if __name__ == "__main__":
    bot.run(TOKEN)