import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class ClearMemberProgressModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Limpar Progresso do Membro")
        self.member_id_input = discord.ui.TextInput(label="ID do Membro", placeholder="Insira o ID do membro", required=True)
        self.add_item(self.member_id_input)

    async def on_submit(self, interaction: discord.Interaction):
        member_id = self.member_id_input.value

        # Verificar se a configuração e o progresso existem
        if not os.path.exists("farmers/member_progress.json"):
            await interaction.response.send_message("Nenhum progresso foi registrado ainda.", ephemeral=True)
            return

        with open("farmers/config.json", "r") as f:
            config = json.load(f)

        # Verificar se o usuário tem o cargo necessário
        if config.get("role_id") not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        member_progress_file = "farmers/member_progress.json"
        with open(member_progress_file, "r") as f:
            progress_data = json.load(f)

        if member_id not in progress_data:
            await interaction.response.send_message(f"Nenhum progresso encontrado para o ID {member_id}.", ephemeral=True)
            return

        # Remover o progresso do membro
        del progress_data[member_id]

        # Salvar o arquivo atualizado
        with open(member_progress_file, "w") as f:
            json.dump(progress_data, f, indent=4)

        # Enviar mensagem confirmando a ação
        await interaction.response.send_message(f"O progresso do membro com ID {member_id} foi removido.", ephemeral=True)

class CheckWeeklyGoalsModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Checar Metas")
        self.bot = bot

        self.member_id_input = discord.ui.TextInput(label="ID do Membro", placeholder="Insira o ID do membro", required=True)
        self.add_item(self.member_id_input)

    async def on_submit(self, interaction: discord.Interaction):
        member_id = self.member_id_input.value

        # Verificar se a configuração e o progresso existem
        if not os.path.exists("farmers/config.json"):
            await interaction.response.send_message("As configurações não foram definidas ainda. Use o comando /cfgfarm.", ephemeral=True)
            return

        if not os.path.exists("farmers/member_progress.json"):
            await interaction.response.send_message("Nenhum progresso foi registrado ainda.", ephemeral=True)
            return

        with open("farmers/config.json", "r") as f:
            config = json.load(f)

        # Verificar se o usuário tem o cargo necessário
        if config.get("role_id") not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        with open("farmers/member_progress.json", "r") as f:
            progress_data = json.load(f)

        log_channel = self.bot.get_channel(interaction.channel_id)  # Canal onde o comando foi digitado
        thumbnail_url = config.get('thumbnail', '')

        if not log_channel:
            await interaction.response.send_message("O canal não foi encontrado. Verifique o ID do canal nas configurações.", ephemeral=True)
            return

        if member_id not in progress_data:
            await interaction.response.send_message(f"Nenhum progresso encontrado para o ID {member_id}.", ephemeral=True)
            return

        member_progress = progress_data[member_id]
        member = self.bot.get_user(int(member_id))

        # Criar a embed com o progresso
        embed = discord.Embed(title=f"Relatório de Metas - {member.name}", color=discord.Color.gold())
        embed.set_thumbnail(url=thumbnail_url)

        for product, data in member_progress.items():
            quantity = data.get("quantidade", 0)
            data_hora = "\n".join([f"{dt}: {quant}" for dt, quant in data.items() if dt != "quantidade"])
            embed.add_field(
                name=f"Produto: {product}",
                value=(
                    f"**Quantidade Total:** {quantity}\n"
                    f"{data_hora}"
                ),
                inline=False
            )

        # Enviar mensagem no canal onde o comando foi digitado
        await log_channel.send(embed=embed)
        
        # Enviar mensagem para o ID do membro fornecido
        if member:
            await member.send(embed=embed)
        
        await interaction.response.send_message("O relatório de metas foi enviado no canal e para o membro solicitado.", ephemeral=True)

class CheckWeeklyGoalsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checarmetas", description="Checa o progresso de todos os membros nas metas semanais")
    async def checarmetas(self, interaction: discord.Interaction):
        # Verificar se a configuração existe
        if not os.path.exists("farmers/config.json"):
            await interaction.response.send_message("As configurações não foram definidas ainda. Use o comando /cfgfarm.", ephemeral=True)
            return

        # Verificar se o usuário tem o cargo necessário
        with open("farmers/config.json", "r") as f:
            config = json.load(f)
        
        if config.get("role_id") not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        # Abrir o modal
        modal = CheckWeeklyGoalsModal(self.bot)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="limparmetas", description="Limpa o progresso de todos os membros")
    async def limparmetas(self, interaction: discord.Interaction):
        # Verificar se o usuário tem o cargo necessário
        with open("farmers/config.json", "r") as f:
            config = json.load(f)
        
        if config.get("role_id") not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        # Limpar o progresso
        member_progress_file = "farmers/member_progress.json"
        if os.path.exists(member_progress_file):
            os.remove(member_progress_file)
            await interaction.response.send_message("O progresso de todos os membros foi limpo.", ephemeral=True)
        else:
            await interaction.response.send_message("Nenhum progresso foi encontrado para limpar.", ephemeral=True)

    @app_commands.command(name="limparmetaid", description="Limpa o progresso de um membro específico")
    async def limparmetaid(self, interaction: discord.Interaction):
        # Verificar se o usuário tem o cargo necessário
        with open("farmers/config.json", "r") as f:
            config = json.load(f)
        
        if config.get("role_id") not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        # Abrir o modal para o ID do membro
        modal = ClearMemberProgressModal()
        await interaction.response.send_modal(modal)

    async def cog_load(self):
        guild_id = 1242127884399673474  # Substitua pelo ID do seu servidor (guild)
        guild = discord.Object(id=guild_id)
        self.bot.tree.add_command(self.checarmetas, guild=guild)
        self.bot.tree.add_command(self.limparmetas, guild=guild)
        self.bot.tree.add_command(self.limparmetaid, guild=guild)

    async def cog_unload(self):
        guild_id = 1242127884399673474  # Substitua pelo ID do seu servidor (guild)
        guild = discord.Object(id=guild_id)
        self.bot.tree.remove_command(self.checarmetas.name, guild=guild)
        self.bot.tree.remove_command(self.limparmetas.name, guild=guild)
        self.bot.tree.remove_command(self.limparmetaid.name, guild=guild)

async def setup(bot):
    await bot.add_cog(CheckWeeklyGoalsCog(bot))
