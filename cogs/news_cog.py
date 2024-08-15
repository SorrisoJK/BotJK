import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput, View

class NewsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="divnoticia", description="Divulgar uma notícia para um cargo específico")
    async def divulgar_noticia(self, interaction: discord.Interaction):
        # Enviar um modal para coletar as informações
        modal = NewsModal(self.bot)
        await interaction.response.send_modal(modal)

class NewsModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Divulgação de Notícia")
        self.bot = bot
        self.add_item(TextInput(label="Título da mensagem", required=True))
        self.add_item(TextInput(label="Link da thumbnail (opcional)", required=False))
        self.add_item(TextInput(label="Link do banner (opcional)", required=False))
        self.add_item(TextInput(label="Conteúdo da mensagem", required=True))
        self.add_item(TextInput(label="ID do cargo", required=True))

    async def on_submit(self, interaction: discord.Interaction):
        title = self.children[0].value.strip()
        thumbnail_url = self.children[1].value.strip()
        banner_url = self.children[2].value.strip()
        content = self.children[3].value
        try:
            role_id = int(self.children[4].value.strip())
        except ValueError:
            await interaction.response.send_message("ID do cargo inválido. Tente novamente.")
            return

        guild = interaction.guild
        role = guild.get_role(role_id)

        if not role:
            await interaction.response.send_message("Cargo não encontrado!")
            return

        embed = discord.Embed(title=title, description=content, color=discord.Color.blue())

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        if banner_url:
            embed.set_image(url=banner_url)

        success_count = 0
        failure_count = 0

        for member in role.members:
            try:
                await member.send(embed=embed)
                success_count += 1
            except discord.Forbidden:
                failure_count += 1

        message = f"Mensagem enviada para {success_count} membros do cargo!", 
        if failure_count > 0:
            message += f" Falha ao enviar para {failure_count} membros."

        # Verificar se a interação ainda está ativa antes de enviar uma resposta
        if not interaction.response.is_done():
            await interaction.response.send_message(message)

async def setup(bot):
    await bot.add_cog(NewsCog(bot))
