import discord
from discord.ext import commands
import json
import os

# Defina o ID do cargo permitido para usar o comando /cfgaction
ROLE_ID = 1242127891857149992  # Substitua pelo ID do cargo desejado

class ActionConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "action/cfgaction.json"
        self.actions_path = "action/acoes.json"

        # Cria a pasta "action" se não existir
        if not os.path.exists("action"):
            os.makedirs("action")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} carregada com sucesso.")

    @discord.app_commands.command(name="cfgaction", description="Configura as opções básicas da ação.")
    async def cfgaction(self, interaction: discord.Interaction):
        """Configura as opções básicas da ação."""
        # Verifica se o usuário tem o cargo necessário
        role = discord.utils.get(interaction.guild.roles, id=ROLE_ID)

        if role in interaction.user.roles:
            modal = ActionConfigModal(self.config_path)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)

    @discord.app_commands.command(name="registraracao", description="Registra uma nova ação.")
    async def registraracao(self, interaction: discord.Interaction):
        """Registra uma nova ação."""
        # Carrega as configurações atuais
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("Configuração não encontrada. Use /cfgaction primeiro.", ephemeral=True)
            return

        # Verifica se o usuário possui o cargo necessário
        role_id = config.get("cargo_role")
        role = discord.utils.get(interaction.guild.roles, id=role_id)

        if role in interaction.user.roles:
            modal = RegisterActionModal(self.actions_path)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)

class ActionConfigModal(discord.ui.Modal):
    def __init__(self, config_path):
        self.config_path = config_path
        super().__init__(title="Configuração de Ação")

        self.add_item(discord.ui.TextInput(label="Canal de Log (ID)", placeholder="123456789012345678"))
        self.add_item(discord.ui.TextInput(label="Cargo (ID)", placeholder="123456789012345678"))
        self.add_item(discord.ui.TextInput(label="URL Thumbnail", placeholder="https://example.com/image.png"))
        self.add_item(discord.ui.TextInput(label="Canal de Ação (ID)", placeholder="123456789012345678"))

    async def on_submit(self, interaction: discord.Interaction):
        # Salva as configurações no arquivo JSON
        config_data = {
            "canal_log": int(self.children[0].value),
            "cargo_role": int(self.children[1].value),
            "url_thumbnail": self.children[2].value,
            "canal_acao": int(self.children[3].value)
        }
        with open(self.config_path, "w") as f:
            json.dump(config_data, f, indent=4)

        await interaction.response.send_message("Configurações salvas com sucesso!", ephemeral=True)

class RegisterActionModal(discord.ui.Modal):
    def __init__(self, actions_path):
        self.actions_path = actions_path
        super().__init__(title="Registrar Ação")

        self.add_item(discord.ui.TextInput(label="Nome da Ação"))
        self.add_item(discord.ui.TextInput(label="Número de Participantes", placeholder="Ex: 8"))
        self.add_item(discord.ui.TextInput(label="Armamento", placeholder="Ex: AUG"))
        self.add_item(discord.ui.TextInput(label="Número de Munição", placeholder="Ex: 250"))
        self.add_item(discord.ui.TextInput(label="Descrição da Ação", style=discord.TextStyle.long))

    async def on_submit(self, interaction: discord.Interaction):
        # Carrega as ações existentes
        if os.path.exists(self.actions_path):
            with open(self.actions_path, "r") as f:
                actions = json.load(f)
        else:
            actions = []

        # Cria o novo registro de ação
        action_data = {
            "nome": self.children[0].value,
            "num_participantes": int(self.children[1].value),
            "armamento": self.children[2].value,
            "num_municao": int(self.children[3].value),
            "descricao": self.children[4].value,
            "autor": interaction.user.name,
            "data": str(discord.utils.utcnow())
        }

        actions.append(action_data)

        # Salva o novo registro no arquivo JSON
        with open(self.actions_path, "w") as f:
            json.dump(actions, f, indent=4)

        await interaction.response.send_message("Ação registrada com sucesso!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ActionConfig(bot))
