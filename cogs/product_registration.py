import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# Verifica se o diretório 'farmers' existe, se não, cria-o
if not os.path.exists("farmers"):
    os.makedirs("farmers")

class ProductRegistrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="registrarproduto", description="Registra um produto e sua quantidade.")
    async def registrarproduto(self, interaction: discord.Interaction, produtos: str, quantidade: int):
        # Carregar produtos existentes
        products_file = "farmers/products.json"
        if os.path.exists(products_file):
            with open(products_file, "r") as f:
                products = json.load(f)
        else:
            products = {}

        # Atualizar produtos
        products[produtos] = quantidade

        # Salvar produtos
        with open(products_file, "w") as f:
            json.dump(products, f, indent=4)

        await interaction.response.send_message(f"Produto '{produtos}' com quantidade '{quantidade}' registrado com sucesso.", ephemeral=True)

    @app_commands.command(name="deletarproduto", description="Remove um produto do registro.")
    async def deletarproduto(self, interaction: discord.Interaction, produto: str):
        products_file = "farmers/products.json"

        if os.path.exists(products_file):
            with open(products_file, "r") as f:
                products = json.load(f)
        else:
            await interaction.response.send_message("Nenhum produto registrado ainda.", ephemeral=True)
            return

        if produto not in products:
            await interaction.response.send_message(f"Produto '{produto}' não encontrado.", ephemeral=True)
            return

        # Remover produto
        del products[produto]

        # Salvar produtos atualizados
        with open(products_file, "w") as f:
            json.dump(products, f, indent=4)

        await interaction.response.send_message(f"Produto '{produto}' removido com sucesso.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProductRegistrationCog(bot))
