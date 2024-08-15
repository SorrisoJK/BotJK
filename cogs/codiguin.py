import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
import json
import os

CONFIG_FILE = 'codiguin_config.json'

# Função para carregar as configurações do arquivo JSON
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

# Função para salvar as configurações no arquivo JSON
def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

class CodiguinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    @app_commands.command(name="cfgcodiguin", description="Configurar cargo, canal de log e thumbnail para codiguins")
    @app_commands.checks.has_role(1242127891857149992)  # Substitua pelo ID real do cargo que pode configurar
    async def cfgcodiguin(self, interaction: discord.Interaction):
        modal = CfgCodiguinModal(self)
        await interaction.response.send_modal(modal)

    @cfgcodiguin.error
    async def cfgcodiguin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message(
                "Você não tem permissão para configurar codiguins.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Ocorreu um erro ao executar este comando.",
                ephemeral=True
            )

    @app_commands.command(name="darcodiguin", description="Enviar um codiguin para um usuário")
    async def darcodiguin(self, interaction: discord.Interaction):
        if not self._can_give_codiguin(interaction.user):
            await interaction.response.send_message("Você não tem permissão para dar um codiguin.", ephemeral=True)
            return
        modal = DarCodiguinModal(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="checkcodiguin", description="Verificar se um membro recebeu codiguin")
    async def checkcodiguin(self, interaction: discord.Interaction):
        modal = CheckCodiguinModal(self)
        await interaction.response.send_modal(modal)

    def _can_give_codiguin(self, member):
        return any(role.id == self.config.get('codiguin_role') for role in member.roles)

class CfgCodiguinModal(Modal):
    def __init__(self, cog):
        super().__init__(title="Configurar Codiguin")
        self.cog = cog
        self.role_input = TextInput(label="ID do Cargo que pode dar Codiguin")
        self.channel_input = TextInput(label="ID do Canal de Log")
        self.thumbnail_input = TextInput(label="URL da Thumbnail", required=False)
        
        self.add_item(self.role_input)
        self.add_item(self.channel_input)
        self.add_item(self.thumbnail_input)

    async def on_submit(self, interaction: discord.Interaction):
        role_id = int(self.role_input.value)
        log_channel_id = int(self.channel_input.value)
        thumbnail_url = self.thumbnail_input.value
        
        self.cog.config['codiguin_role'] = role_id
        self.cog.config['log_channel'] = log_channel_id
        self.cog.config['thumbnail_url'] = thumbnail_url
        save_config(self.cog.config)
        
        await interaction.response.send_message("Configurações salvas com sucesso!", ephemeral=True)

class DarCodiguinModal(Modal):
    def __init__(self, cog):
        super().__init__(title="Dar Codiguin")
        self.cog = cog
        self.user_id_input = TextInput(label="ID do Discord da Pessoa")
        self.codiguin_input = TextInput(label="Codiguin")
        self.message_input = TextInput(label="Mensagem na Embed", style=discord.TextStyle.long)
        
        self.add_item(self.user_id_input)
        self.add_item(self.codiguin_input)
        self.add_item(self.message_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = int(self.user_id_input.value)
        codiguin = self.codiguin_input.value
        message = self.message_input.value
        
        user = await self.cog.bot.fetch_user(user_id)
        log_channel = self.cog.bot.get_channel(self.cog.config['log_channel'])
        thumbnail_url = self.cog.config.get('thumbnail_url')
        
        # Cria a embed com o codiguin em negrito e em destaque
        embed = discord.Embed(
            title="Parabéns, você ganhou um codiguin!",
            description=message,
            color=discord.Color.green()
        )
        embed.add_field(
            name="Codiguin",
            value=f"**`{codiguin}`**",  # Codiguin em negrito e destacado
            inline=False
        )
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        
        # Envia a embed para a pessoa
        await user.send(embed=embed)
        
        # Loga o codiguin no canal de log
        await log_channel.send(f"{user.mention} recebeu um codiguin de {interaction.user.mention}", embed=embed)
        
        # Salva a transação no JSON
        if 'transactions' not in self.cog.config:
            self.cog.config['transactions'] = []
        
        self.cog.config['transactions'].append({
            'user_id': user_id,
            'codiguin': codiguin,
            'giver_id': interaction.user.id,
            'message': message
        })
        save_config(self.cog.config)
        
        await interaction.response.send_message("Codiguin enviado com sucesso!", ephemeral=True)

class CheckCodiguinModal(Modal):
    def __init__(self, cog):
        super().__init__(title="Checar Codiguin")
        self.cog = cog
        self.user_id_input = TextInput(label="ID do Membro")
        
        self.add_item(self.user_id_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = int(self.user_id_input.value)
        transactions = [t for t in self.cog.config.get('transactions', []) if t['user_id'] == user_id]
        
        if not transactions:
            await interaction.response.send_message("Este usuário não recebeu nenhum codiguin.", ephemeral=True)
            return
        
        messages = []
        for t in transactions:
            codiguin = t.get('codiguin', 'Não especificado')
            giver_id = t.get('giver_id', 'Desconhecido')
            message = t.get('message', 'Nenhuma mensagem fornecida')
            messages.append(f"Codiguin: **`{codiguin}`** - Dado por: <@{giver_id}> - Mensagem: {message}")
        
        await interaction.response.send_message("\n".join(messages), ephemeral=True)

async def setup(bot):
    await bot.add_cog(CodiguinCog(bot))
