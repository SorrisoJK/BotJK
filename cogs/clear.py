import discord
from discord.ext import commands
from discord import app_commands

ROLE_ID = 123456789012345678  # Substitua pelo ID real do cargo

class Clear(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='clear', description='Apaga um número específico de mensagens no canal atual.')
    @app_commands.describe(quantidade='Número de mensagens a serem apagadas (1-100)')
    async def clear(self, interaction: discord.Interaction, quantidade: int):
        """Apaga um número específico de mensagens no canal atual (mínimo 1, máximo 100)."""
        # Verificação do cargo
        if not any(role.id == ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        if quantidade < 1 or quantidade > 100:
            await interaction.response.send_message("Por favor, forneça um número entre 1 e 100.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        deleted = await interaction.channel.purge(limit=quantidade)
        
        await interaction.followup.send(f'{len(deleted)} mensagens apagadas.', ephemeral=True)

    @app_commands.command(name='wipeall', description='Apaga todos os canais e os recria com as mesmas permissões.')
    async def wipeall(self, interaction: discord.Interaction):
        """Apaga todos os canais de texto e os recria com as mesmas permissões."""
        # Verificação do cargo
        if not any(role.id == ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        channel_data = []

        # Fazer backup dos canais e suas permissões
        for channel in guild.text_channels:
            channel_data.append({
                'name': channel.name,
                'category': channel.category,
                'position': channel.position,
                'overwrites': channel.overwrites,
                'topic': channel.topic,
                'nsfw': channel.is_nsfw(),
                'slowmode_delay': channel.slowmode_delay,
            })

        # Apagar todos os canais de texto
        for channel in guild.text_channels:
            await channel.delete()

        # Recriar os canais com as mesmas permissões e configurações
        for data in channel_data:
            new_channel = await guild.create_text_channel(
                name=data['name'],
                category=data['category'],
                position=data['position'],
                overwrites=data['overwrites'],
                topic=data['topic'],
                nsfw=data['nsfw'],
                slowmode_delay=data['slowmode_delay']
            )

        await interaction.followup.send('Todos os canais foram apagados e recriados com sucesso!', ephemeral=True)

async def setup(bot):
    await bot.add_cog(Clear(bot))
    await bot.tree.sync()  # Sincroniza os comandos de barra com o Discord
