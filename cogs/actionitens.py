import discord
from discord.ext import commands
import json
import os

class ActionItems(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.actions_path = "action/acoes.json"
        self.config_path = "action/cfgaction.json"
        self.active_topics = {}

        # Carrega a configuração do arquivo cfgaction.json
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Arquivo {self.config_path} não encontrado.")
            return {}

    def has_permission(self, member: discord.Member):
        # Obtém o ID do cargo necessário para usar os comandos
        required_role_id = self.config.get("cargo_role")

        # Verifica se o membro possui o cargo necessário
        return any(role.id == required_role_id for role in member.roles)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} carregada com sucesso.")

    @discord.app_commands.command(name="selectaction", description="Seleciona uma ação e cria um tópico no canal.")
    async def selectaction(self, interaction: discord.Interaction):
        """Seleciona uma ação e cria um tópico no canal."""
        if not self.has_permission(interaction.user):
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        try:
            with open(self.actions_path, "r") as f:
                actions = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("Nenhuma ação registrada encontrada.", ephemeral=True)
            return

        # Cria as opções do Select Menu
        options = []
        for idx, action in enumerate(actions):
            options.append(discord.SelectOption(label=action["nome"], description=action["descricao"], value=str(idx)))

        # Cria o Select Menu
        select = ActionTopicSelect(actions, self)
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("Selecione uma ação para criar um tópico:", view=view, ephemeral=True)

    async def create_topic(self, interaction: discord.Interaction, action):
        """Cria um tópico no canal com as informações da ação."""
        channel = interaction.channel

        # Nome do tópico, verificando se já existe para adicionar um número ao final
        base_topic_name = action["nome"]
        topic_name = base_topic_name
        topic_count = 1
        while topic_name in self.active_topics.get(channel.id, []):
            topic_count += 1
            topic_name = f"{base_topic_name} #{topic_count}"

        # Cria o tópico no canal
        topic = await channel.create_thread(name=topic_name, type=discord.ChannelType.public_thread)

        # Registra o tópico ativo
        if channel.id not in self.active_topics:
            self.active_topics[channel.id] = []
        self.active_topics[channel.id].append(topic_name)

        # Envia a embed com as informações da ação no tópico
        embed = discord.Embed(
            title=action["nome"],
            description=action["descricao"],
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=action.get("url_thumbnail", ""))
        embed.add_field(name="Armamento", value=action["armamento"], inline=True)
        embed.add_field(name="Munição", value=action["num_municao"], inline=True)

        await topic.send(embed=embed)
        await interaction.followup.send(f"Tópico '{topic_name}' criado com sucesso.", ephemeral=True)

    @discord.app_commands.command(name="entregaitens", description="Entrega itens a um membro em um tópico.")
    @discord.app_commands.describe(member="O membro que receberá os itens", armamento="Nome da arma entregue", municao="Quantidade de munição entregue", outros="Outros itens entregues")
    async def entregaitens(self, interaction: discord.Interaction, member: discord.Member, armamento: str, municao: int, outros: str = None):
        """Entrega itens a um membro em um tópico."""
        if not self.has_permission(interaction.user):
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        thread = interaction.channel
        if not isinstance(thread, discord.Thread) or thread not in [t for t in thread.parent.threads if t.id == thread.id]:
            await interaction.response.send_message("Este comando só pode ser usado dentro de um tópico ativo.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Itens Entregues",
            color=discord.Color.green()
        )
        embed.add_field(name="Membro", value=member.mention, inline=True)
        embed.add_field(name="Armamento", value=armamento, inline=True)
        embed.add_field(name="Munição", value=str(municao), inline=True)
        if outros:
            embed.add_field(name="Outros", value=outros, inline=True)

        await thread.send(embed=embed)
        await interaction.response.send_message(f"Itens entregues para {member.mention}.", ephemeral=True)


class ActionTopicSelect(discord.ui.Select):
    def __init__(self, actions, cog):
        self.actions = actions
        self.cog = cog

        options = [
            discord.SelectOption(label=action["nome"], description=action["descricao"], value=str(i))
            for i, action in enumerate(actions)
        ]
        super().__init__(placeholder="Selecione uma ação...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_action_index = int(self.values[0])
        action = self.actions[selected_action_index]
        
        # Responde à interação imediatamente
        await interaction.response.defer(ephemeral=True)
        
        # Cria o tópico
        await self.cog.create_topic(interaction, action)


async def setup(bot):
    await bot.add_cog(ActionItems(bot))
