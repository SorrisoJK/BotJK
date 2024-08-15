import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select, Modal, TextInput
import json
import os

# Função para garantir que o diretório e o arquivo existam
def ensure_json_file_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({}, f)

# Modal para adicionar progresso
class FarmerProgressModal(Modal):
    def __init__(self, product_name, member_id):
        super().__init__(title=f"Adicionar Progresso - {product_name}")
        self.product_name = product_name
        self.member_id = member_id

        self.progresso = TextInput(label="Quantidade Adicionada", placeholder="Insira a quantidade", required=True)
        self.data_hora = TextInput(label="Data e Hora", placeholder="Exemplo: 11/08/2024 14:30", required=True)

        self.add_item(self.progresso)
        self.add_item(self.data_hora)

    async def on_submit(self, interaction: discord.Interaction):
        # Carregar progresso existente
        member_progress_file = "farmers/member_progress.json"
        ensure_json_file_exists(member_progress_file)

        with open(member_progress_file, "r") as f:
            member_progress = json.load(f)

        if self.member_id not in member_progress:
            member_progress[self.member_id] = {}

        # Atualizar progresso
        if self.product_name not in member_progress[self.member_id]:
            member_progress[self.member_id][self.product_name] = {"quantidade": 0}

        # Adicionar a quantidade adicional
        quantidade_adicionada = int(self.progresso.value)
        member_progress[self.member_id][self.product_name]["quantidade"] += quantidade_adicionada
        member_progress[self.member_id][self.product_name][self.data_hora.value] = quantidade_adicionada

        # Salvar progresso
        with open(member_progress_file, "w") as f:
            json.dump(member_progress, f, indent=4)

        await interaction.response.send_message(f"O <@{self.member_id}> adicionou {quantidade_adicionada} unidades do produto `{self.product_name}` em {self.data_hora.value}", ephemeral=False)


# Menu de seleção de produtos
class ProductSelectMenu(Select):
    def __init__(self, products, member_id):
        options = [discord.SelectOption(label=product, description=f"Registrar progresso para {product}") for product in products if product]
        if not options:
            options = [discord.SelectOption(label="Nenhum produto disponível", value="none")]
        super().__init__(placeholder="Selecione o produto...", options=options)
        self.member_id = member_id

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Nenhum produto disponível para registrar progresso.", ephemeral=True)
            return
        modal = FarmerProgressModal(self.values[0], self.member_id)
        await interaction.response.send_modal(modal)

# View para adicionar progresso
class FarmerProgressView(View):
    def __init__(self, products, member_id):
        super().__init__(timeout=None)
        self.add_item(ProductSelectMenu(products, member_id))

# View para criar canal de farmer
class CreateFarmerChannelButton(View):
    def __init__(self, category_id, role_id, thumbnail_url, goals):
        super().__init__(timeout=None)
        self.category_id = category_id
        self.role_id = role_id
        self.thumbnail_url = thumbnail_url
        self.goals = goals

        self.create_button = Button(label="Abrir Canal de Farm", style=discord.ButtonStyle.primary)
        self.create_button.callback = self.create_channel
        self.add_item(self.create_button)

    async def create_channel(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Interação inválida.", ephemeral=True)
            return

        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=self.category_id)
        role = guild.get_role(self.role_id)

        if not category or not role:
            await interaction.response.send_message("Erro na configuração da categoria ou cargo.", ephemeral=True)
            return

        # Verificar se o membro já tem um canal criado
        existing_channel = discord.utils.get(category.channels, name=f"farm-{interaction.user.name}")
        if existing_channel:
            await interaction.response.send_message(f"Você já possui um canal criado: {existing_channel.mention}", ephemeral=True)
            return

        # Criar o canal se não existir
        channel_name = f"farm-{interaction.user.name}"
        channel = await guild.create_text_channel(channel_name, category=category)

        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await channel.set_permissions(role, read_messages=True, send_messages=True)
        await channel.set_permissions(guild.default_role, read_messages=False)

        # Atualizar embed com metas
        embed = discord.Embed(title="Sua meta Semanal 📦", color=discord.Color.green())
        embed.set_thumbnail(url=self.thumbnail_url)

        for product, goal in self.goals.items():
            embed.add_field(name=product, value=f"Meta: {goal}", inline=False)

        embed.set_footer(text="Você pode continuar farmando após bater a meta para receber um extra 😉")

        # Enviar mensagem com embed e view
        products = list(self.goals.keys())
        view = FarmerProgressView(products, str(interaction.user.id))

        try:
            print(f"Enviando mensagem para o canal {channel.id} com a embed.")
            await channel.send(embed=embed, view=view)
            print("Mensagem enviada com sucesso.")
        except discord.HTTPException as e:
            print(f"Erro ao enviar mensagem para o canal: {e}")

        await interaction.response.send_message(f"Canal criado com sucesso: {channel.mention}", ephemeral=True)

# Modal para registrar pagamento
class PayFarmModal(Modal):
    def __init__(self, log_channel_id, role_id, thumbnail_url):
        super().__init__(title="Pagamento de Farm")
        self.log_channel_id = log_channel_id
        self.role_id = role_id
        self.thumbnail_url = thumbnail_url

        self.member_id = TextInput(label="ID do Membro", placeholder="Insira o ID do membro", required=True)
        self.valor_pago = TextInput(label="Valor Pago", placeholder="Insira o valor pago", required=True)
        self.banner_url = TextInput(label="URL do Banner", placeholder="Insira a URL do banner", required=True)

        self.add_item(self.member_id)
        self.add_item(self.valor_pago)
        self.add_item(self.banner_url)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = guild.get_member(int(self.member_id.value))
        if not member:
            await interaction.response.send_message(f"Membro com ID {self.member_id.value} não encontrado.", ephemeral=True)
            return

        # Criar a embed
        embed = discord.Embed(title="Pagamento de Farm Realizado 💸", color=discord.Color.gold())
        embed.set_thumbnail(url=self.thumbnail_url)
        embed.add_field(name="Membro", value=f"<@{self.member_id.value}>", inline=False)
        embed.add_field(name="Valor Pago", value=self.valor_pago.value, inline=False)
        embed.set_image(url=self.banner_url.value)
        embed.add_field(name="Pagamento realizado por", value=f"{interaction.user.mention}", inline=False)

        # Enviar a embed no canal de log
        log_channel = guild.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)
        
        # Enviar a embed na DM do membro
        try:
            await member.send(embed=embed)
            await interaction.response.send_message(f"Pagamento registrado com sucesso e notificado ao membro <@{self.member_id.value}>.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"Não foi possível enviar DM para o membro <@{self.member_id.value}>, mas o pagamento foi registrado.", ephemeral=True)


# Cog de Gerenciamento de Farmers
class FarmerManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, interaction: discord.Interaction, config_file: str):
        if not os.path.exists(config_file):
            await interaction.response.send_message("As configurações não foram definidas ainda. Use o comando /cfgfarm.", ephemeral=True)
            return False

        with open(config_file, "r") as f:
            config = json.load(f)

        role = interaction.guild.get_role(config["role_id"])
        if role not in interaction.user.roles:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return False

        return config

    @app_commands.command(name="bfarm", description="Cria um canal pessoal para o farm")
    async def bfarm(self, interaction: discord.Interaction):
        config_file = "farmers/config.json"
        goals_file = "farmers/products.json"

        config = await self.check_permissions(interaction, config_file)
        if not config:
            return

        if not os.path.exists(goals_file):
            await interaction.response.send_message("As metas não foram definidas ainda. Use o comando /registrarproduto.", ephemeral=True)
            return

        with open(goals_file, "r") as f:
            goals = json.load(f)

        embed = discord.Embed(title="Metas de farm 📦", color=discord.Color.blue())
        embed.set_thumbnail(url=config['thumbnail'])
        embed.description = "Clique no botão abaixo para criar seu canal de farm."

        view = CreateFarmerChannelButton(config["category_id"], config["role_id"], config["thumbnail"], goals)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="pagarfarm", description="Registra um pagamento de farm para um membro.")
    async def pagarfarm(self, interaction: discord.Interaction):
        config_file = "farmers/config.json"

        config = await self.check_permissions(interaction, config_file)
        if not config:
            return

        modal = PayFarmModal(config["log_channel_id"], config["role_id"], config["thumbnail"])
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(FarmerManagementCog(bot))
