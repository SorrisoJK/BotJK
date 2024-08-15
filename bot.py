import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            except Exception as e:
                print(f'Erro ao carregar extensão {filename[:-3]}: {e}')

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    await load_cogs()  # Chama a função para carregar os cogs

    # Sincroniza os comandos de barra
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizado {len(synced)} comandos de barra globalmente.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos de barra: {e}")

bot.run('token')
