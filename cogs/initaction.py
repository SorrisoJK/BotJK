import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput, Select
import json
import aiojobs
import asyncio
from datetime import datetime, timedelta

class InitAction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "action/cfgaction.json"
        self.actions_path = "action/acoes.json"
        self.participants = {}  # Dicionário para armazenar os participantes das ações
        self.scheduler = None  # Inicializa o scheduler

    @commands.Cog.listener()
    async def on_ready(self):
        self.scheduler = await aiojobs.create_scheduler()
        print(f"{self.__class__.__name__} carregada com sucesso.")

    @discord.app_commands.command(name="baction", description="Inicia uma ação.")
    async def baction(self, interaction: discord.Interaction):
        """Inicia uma ação."""
        # Carrega as configurações
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            await interaction.response.send_message("Configuração não encontrada. Use /cfgaction primeiro.", ephemeral=True)
            return

        # Cria a embed para a ação
        embed = discord.Embed(
            title="Marcar Ação",
            description="Clique no botão abaixo para marcar uma ação.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=config["url_thumbnail"])

        # Cria o botão para registrar a ação
        view = RegisterActionView(self.actions_path, config["canal_acao"], self.participants, config, self.bot, self.scheduler)
        await interaction.response.send_message(embed=embed, view=view)

class RegisterActionView(View):
    def __init__(self, actions_path, action_channel_id, participants, config, bot, scheduler):
        super().__init__()
        self.actions_path = actions_path
        self.action_channel_id = action_channel_id
        self.participants = participants
        self.config = config
        self.bot = bot
        self.scheduler = scheduler  # Armazena o scheduler para agendar os lembretes

    @discord.ui.button(label="Registrar Ação", style=discord.ButtonStyle.primary)
    async def register_action_button(self, interaction: discord.Interaction, button: Button):
        # Carrega as ações disponíveis
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
        select = ActionSelect(actions, self.action_channel_id, self.participants, self.config, self.bot, self.scheduler)
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Selecione uma ação:", view=view, ephemeral=True)

class ActionSelect(Select):
    def __init__(self, actions, action_channel_id, participants, config, bot, scheduler):
        self.actions = actions
        self.action_channel_id = action_channel_id
        self.participants = participants
        self.config = config
        self.bot = bot
        self.scheduler = scheduler  # Armazena o scheduler

        options = [
            discord.SelectOption(label=action["nome"], description=action["descricao"], value=str(i))
            for i, action in enumerate(actions)
        ]
        super().__init__(placeholder="Selecione uma ação...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_action_index = int(self.values[0])
        action = self.actions[selected_action_index]

        # Inicializa a lista de participantes se não estiver no dicionário
        if action["nome"] not in self.participants:
            self.participants[action["nome"]] = []

        # Abre o modal para definir a hora da ação
        modal = ActionTimeModal(action, self.participants, self.config, self.bot, self.scheduler)
        await interaction.response.send_modal(modal)

class ActionTimeModal(Modal):
    def __init__(self, action, participants, config, bot, scheduler):
        super().__init__(title="Definir Hora da Ação")
        self.action = action
        self.participants = participants
        self.config = config
        self.bot = bot
        self.scheduler = scheduler

        self.add_item(TextInput(label="Hora da Ação", placeholder="SÓ É VALIDO DAS 00H AS 23"))

    async def on_submit(self, interaction: discord.Interaction):
        hora_acao = self.children[0].value.strip()

        # Cria a embed com as informações da ação
        embed = discord.Embed(
            title=self.action["nome"],
            description=self.action["descricao"],
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=self.config["url_thumbnail"])
        embed.add_field(name="Armamento", value=self.action["armamento"], inline=True)
        embed.add_field(name="Munição", value=self.action["num_municao"], inline=True)
        embed.add_field(name="Hora da Ação", value=hora_acao, inline=True)
        embed.add_field(name="Participantes", value=f"{len(self.participants[self.action['nome']])}/{self.action['num_participantes']}", inline=True)

        # Botões de ação
        view = ActionParticipateView(self.action, self.participants, self.config, self.bot, self.scheduler, hora_acao)

        # Envia a embed no canal configurado
        action_channel = interaction.guild.get_channel(self.config["canal_acao"])
        if action_channel:
            await action_channel.send(embed=embed, view=view)
            await interaction.response.send_message("Ação iniciada no canal designado.", ephemeral=True)
        else:
            await interaction.response.send_message("Canal de ação configurado não encontrado.", ephemeral=True)

class ActionParticipateView(View):
    def __init__(self, action, participants, config, bot, scheduler, hora_acao):
        super().__init__(timeout=None)  # Sem timeout para que os botões permaneçam ativos
        self.action = action
        self.participants = participants
        self.config = config
        self.bot = bot
        self.scheduler = scheduler
        self.hora_acao = hora_acao

    @discord.ui.button(label="Participar da Ação", style=discord.ButtonStyle.success)
    async def participate_button(self, interaction: discord.Interaction, button: Button):
        participant_list = self.participants[self.action["nome"]]

        if interaction.user.mention in participant_list:
            await interaction.response.send_message("Você já está registrado nesta ação.", ephemeral=True)
        elif len(participant_list) >= self.action["num_participantes"]:
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("Número máximo de participantes atingido.", ephemeral=True)
        else:
            participant_list.append(interaction.user.mention)
            embed = interaction.message.embeds[0]
            embed.set_field_at(3, name="Participantes", value=f"{len(participant_list)}/{self.action['num_participantes']}", inline=True)
            await interaction.message.edit(embed=embed)
            await interaction.response.send_message("Você foi adicionado à ação.", ephemeral=True)

            # Desabilita o botão se o limite de participantes for atingido
            if len(participant_list) >= self.action["num_participantes"]:
                button.disabled = True
                await interaction.message.edit(view=self)

            # Agenda os lembretes para o participante
            await self.schedule_reminders(interaction.user, self.hora_acao)

    @discord.ui.button(label="Ver Participantes", style=discord.ButtonStyle.secondary)
    async def view_participants_button(self, interaction: discord.Interaction, button: Button):
        participant_list = self.participants[self.action["nome"]]

        if participant_list:
            participants_str = "\n".join(participant_list)
            await interaction.response.send_message(f"**Participantes:**\n{participants_str}", ephemeral=True)
        else:
            await interaction.response.send_message("Ainda não há participantes registrados.", ephemeral=True)

    @discord.ui.button(label="Encerrar Ação", style=discord.ButtonStyle.danger)
    async def end_action_button(self, interaction: discord.Interaction, button: Button):
        # Verifica se o usuário tem permissão para encerrar a ação (por exemplo, um administrador ou o autor)
        required_role_id = self.config.get("cargo_role")
        if required_role_id:
            role = discord.utils.get(interaction.guild.roles, id=required_role_id)
            if role in interaction.user.roles:
                modal = EndActionModal(self.action, self.participants, interaction.message, self.config, self.bot)
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.send_message("Você não tem permissão para encerrar esta ação.", ephemeral=True)
        else:
            await interaction.response.send_message("Cargo de permissão não configurado.", ephemeral=True)

    async def schedule_reminders(self, user, hora_acao):
        # Verifica se o scheduler foi inicializado
        if self.scheduler is None:
            self.scheduler = await aiojobs.create_scheduler()

        # Converte a hora da ação para um objeto datetime
        action_time = datetime.strptime(hora_acao, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )

        # Calcula o tempo para os lembretes
        reminder_times = {
            "30 minutos antes": action_time - timedelta(minutes=30),
            "5 minutos antes": action_time - timedelta(minutes=5)
        }

        for reminder, reminder_time in reminder_times.items():
            if reminder_time > datetime.now():
                await self.scheduler.spawn(self.send_reminder(user, reminder_time, reminder))


    async def send_reminder(self, user, reminder_time, reminder):
        # Espera até o horário do lembrete
        await discord.utils.sleep_until(reminder_time)

        # Envia a mensagem direta ao usuário
        message = f"**Lembrete:** A ação '{self.action['nome']}' está marcada para começar em {reminder}. "
        if reminder == "30 minutos antes":
            message += "Por favor, esteja preparado. Caso você falte sem aviso, poderá ser punido."
        else:
            message += "É hora de se preparar! Se precisar de algo para a ação ou tiver dúvidas, pergunte a algum staff."

        try:
            await user.send(message)
        except discord.Forbidden:
            print(f"Não foi possível enviar a mensagem para {user.name}. Eles podem ter desativado DMs.")

class EndActionModal(Modal):
    def __init__(self, action, participants, action_message, config, bot):
        super().__init__(title="Encerrar Ação")
        self.action = action
        self.participants = participants
        self.action_message = action_message
        self.config = config
        self.bot = bot

        self.add_item(TextInput(label="Resultado (Ganhou/Perdeu)", placeholder="Ganhou"))
        self.add_item(TextInput(label="Dinheiro Arrecadado", placeholder="Ex: 5000"))

    async def on_submit(self, interaction: discord.Interaction):
        resultado = self.children[0].value.strip().lower()
        dinheiro = self.children[1].value.strip()

        # Define a cor da embed baseada no resultado
        if resultado == "ganhou":
            color = discord.Color.green()
        elif resultado == "perdeu":
            color = discord.Color.red()
        else:
            await interaction.response.send_message("Resultado inválido. Use 'Ganhou' ou 'Perdeu'.", ephemeral=True)
            return

        # Cria a embed de log
        embed = discord.Embed(
            title=f"Ação Encerrada: {self.action['nome']}",
            color=color
        )
        embed.set_thumbnail(url=self.config["url_thumbnail"])
        embed.add_field(name="Resultado", value=resultado.capitalize(), inline=True)
        embed.add_field(name="Dinheiro Arrecadado", value=f"${dinheiro}", inline=True)
        embed.add_field(name="Participantes", value="\n".join(self.participants[self.action["nome"]]) or "Nenhum", inline=False)

        # Envia a embed no canal de log
        log_channel = interaction.guild.get_channel(self.config["canal_log"])
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            await interaction.response.send_message("Canal de log configurado não encontrado.", ephemeral=True)
            return

        # Deleta a mensagem original da ação
        await self.action_message.delete()

        # Limpa a lista de participantes
        self.participants[self.action["nome"]] = []

        await interaction.response.send_message("Ação encerrada e registrada no canal de log.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(InitAction(bot))
