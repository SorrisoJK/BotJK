import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# Função para carregar e salvar o arquivo JSON
def load_config():
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as f:
            json.dump({}, f)
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='cfgverify', description='Configura as opções de verificação.')
    @app_commands.default_permissions(administrator=True)
    async def cfgverify(self, interaction: discord.Interaction):
        # Criar modal para configurar
        class ConfigModal(discord.ui.Modal, title='Configuração de Verificação'):
            cargo_id = discord.ui.TextInput(label='ID do Cargo', required=True)
            cargo_aprovacao_id = discord.ui.TextInput(label='ID do Cargo de Aprovação', required=True)
            canal_onde = discord.ui.TextInput(label='ID do Canal para Embed', required=True)
            canal_aprovacao = discord.ui.TextInput(label='ID do Canal de Aprovação', required=True)
            canal_log = discord.ui.TextInput(label='ID do Canal de Log', required=True)

            async def on_submit(self, interaction: discord.Interaction):
                config = load_config()
                config[str(interaction.guild_id)] = {
                    'cargo_id': int(self.cargo_id.value),
                    'cargo_aprovacao_id': int(self.cargo_aprovacao_id.value),
                    'canal_onde': int(self.canal_onde.value),
                    'canal_aprovacao': int(self.canal_aprovacao.value),
                    'canal_log': int(self.canal_log.value)
                }
                save_config(config)
                await interaction.response.send_message('Configuração salva com sucesso!', ephemeral=True)

        await interaction.response.send_modal(ConfigModal())

    @app_commands.command(name='btverify', description='Cria uma verificação por botão.')
    @app_commands.default_permissions(administrator=True)
    async def btverify(self, interaction: discord.Interaction):
        # Carregar a configuração atual
        config = load_config().get(str(interaction.guild_id))
        if not config:
            await interaction.response.send_message('A configuração não foi encontrada. Use /cfgverify primeiro.', ephemeral=True)
            return

        # Criar modal para configuração da embed
        class EmbedModal(discord.ui.Modal, title='Criação de Embed'):
            def __init__(self, bot):
                super().__init__()
                self.bot = bot

            titulo = discord.ui.TextInput(label='Título da Embed', required=True)
            descricao = discord.ui.TextInput(label='Descrição da Embed', style=discord.TextStyle.long, required=True)
            thumbnail_url = discord.ui.TextInput(label='URL do Thumbnail', required=True)

            async def on_submit(self, interaction: discord.Interaction):
                embed = discord.Embed(title=self.titulo.value, description=self.descricao.value, color=discord.Color.blue())
                embed.set_thumbnail(url=self.thumbnail_url.value)
                
                button = discord.ui.Button(label='Registro', style=discord.ButtonStyle.primary)

                async def button_callback(interaction: discord.Interaction):
                    # Criar modal para registro de informações
                    class RegistroModal(discord.ui.Modal, title='Registro'):
                        def __init__(self, bot):
                            super().__init__()
                            self.bot = bot

                        nome = discord.ui.TextInput(label='Seu Nome', required=True)
                        id_ingame = discord.ui.TextInput(label='ID Ingame', required=True)
                        phone_ingame = discord.ui.TextInput(label='Phone Ingame', required=True)
                        recrutador = discord.ui.TextInput(label='Recrutador', required=True)

                        async def on_submit(self, interaction: discord.Interaction):
                            # Mudar o apelido do usuário
                            novo_apelido = f"{self.nome.value} | {self.id_ingame.value}"
                            await interaction.user.edit(nick=novo_apelido)

                            approval_embed = discord.Embed(
                                title='Nova Solicitação de Registro',
                                color=discord.Color.orange()
                            )
                            approval_embed.add_field(name='Nome', value=self.nome.value, inline=False)
                            approval_embed.add_field(name='ID Ingame', value=self.id_ingame.value, inline=False)
                            approval_embed.add_field(name='Phone Ingame', value=self.phone_ingame.value, inline=False)
                            approval_embed.add_field(name='Recrutador', value=self.recrutador.value, inline=False)
                            
                            # Canal de aprovação
                            canal_aprovacao = self.bot.get_channel(config['canal_aprovacao'])
                            
                            # Criar botões de aprovação e recusa
                            approve_button = discord.ui.Button(label='Aprovar', style=discord.ButtonStyle.success)
                            reject_button = discord.ui.Button(label='Recusar', style=discord.ButtonStyle.danger)

                            async def approve_callback(interaction: discord.Interaction):
                                # Atribuir o cargo de aprovação ao usuário que preencheu o modal
                                member = interaction.guild.get_member(self.original_interaction.user.id)
                                role_aprovacao = interaction.guild.get_role(config['cargo_aprovacao_id'])
                                await member.add_roles(role_aprovacao)

                                # Enviar para o canal de log
                                log_channel = self.bot.get_channel(config['canal_log'])
                                log_embed = discord.Embed(
                                    title='Usuário Aprovado',
                                    description=f'{self.nome.value} foi aprovado por {interaction.user.mention}',
                                    color=discord.Color.green()
                                )
                                log_embed.add_field(name='Nome', value=self.nome.value, inline=False)
                                log_embed.add_field(name='ID Ingame', value=self.id_ingame.value, inline=False)
                                log_embed.add_field(name='Phone Ingame', value=self.phone_ingame.value, inline=False)
                                log_embed.add_field(name='Recrutador', value=self.recrutador.value, inline=False)
                                log_embed.add_field(name='Aprovado por', value=interaction.user.mention, inline=False)
                                await log_channel.send(embed=log_embed)
                                await interaction.response.send_message('Usuário aprovado e cargo atribuído!', ephemeral=True)

                            async def reject_callback(interaction: discord.Interaction):
                                # Enviar para o canal de log
                                log_channel = self.bot.get_channel(config['canal_log'])
                                log_embed = discord.Embed(
                                    title='Usuário Reprovado',
                                    description=f'{self.nome.value} foi reprovado por {interaction.user.mention}',
                                    color=discord.Color.red()
                                )
                                log_embed.add_field(name='Nome', value=self.nome.value, inline=False)
                                log_embed.add_field(name='ID Ingame', value=self.id_ingame.value, inline=False)
                                log_embed.add_field(name='Phone Ingame', value=self.phone_ingame.value, inline=False)
                                log_embed.add_field(name='Recrutador', value=self.recrutador.value, inline=False)
                                log_embed.add_field(name='Reprovado por', value=interaction.user.mention, inline=False)
                                await log_channel.send(embed=log_embed)
                                await interaction.response.send_message('Usuário reprovado!', ephemeral=True)
                            
                            approve_button.callback = approve_callback
                            reject_button.callback = reject_callback

                            view = discord.ui.View()
                            view.add_item(approve_button)
                            view.add_item(reject_button)

                            # Guardar a interação original para uso posterior
                            self.original_interaction = interaction

                            await canal_aprovacao.send(embed=approval_embed, view=view)
                            await interaction.response.send_message('Registro enviado para aprovação.', ephemeral=True)

                    await interaction.response.send_modal(RegistroModal(bot=self.bot))

                button.callback = button_callback
                view = discord.ui.View()
                view.add_item(button)

                # Canal onde a embed será enviada
                canal_onde = self.bot.get_channel(config['canal_onde'])
                await canal_onde.send(embed=embed, view=view)
                await interaction.response.send_message('Embed criada com sucesso!', ephemeral=True)

        await interaction.response.send_modal(EmbedModal(bot=self.bot))

async def setup(bot):
    await bot.add_cog(VerifyCog(bot))
