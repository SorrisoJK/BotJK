import discord
from discord.ext import commands
from discord.ui import Button, View

# IDs dos canais e cargos
SUGGESTIONS_CHANNEL_ID = 1242129022717001808
ALLOWED_ROLE_IDS = [
    1242127891857149992,
    222222222222222222,
    333333333333333333,
]

# URL da imagem para a thumbnail da sugestão
THUMBNAIL_URL = 'https://media.discordapp.net/attachments/998288964156923904/1265169352672415786/Logo_Animada_GIF_15_FPS_mmb.gif?ex=66b5a047&is=66b44ec7&hm=ed3dcbeec3cb0fb1346496629e8e37f022aa9d329dcc0f9d05bb41acff65fc50&=&width=350&height=350'

# Armazenamento de votos
votes = {}

class Sugestao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog 'sugestao' carregado com sucesso.")

    @discord.app_commands.command(name="setsugestao", description="Crie uma sugestão para melhorar o servidor.")
    async def setsugestao(self, interaction: discord.Interaction):
        if not any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles):
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        embed = discord.Embed(
            title="📢 **Sua Sugestão é Valiosa!**",
            description="Estamos sempre em busca de melhorias para nosso servidor. Clique no botão abaixo para enviar a sua sugestão.",
            color=0x00aaff
        )
        embed.set_footer(text="Obrigado por ajudar a tornar nosso servidor melhor!")
        embed.set_thumbnail(url=THUMBNAIL_URL)

        button = Button(label="Enviar Sugestão", style=discord.ButtonStyle.primary)

        async def button_callback(interaction: discord.Interaction):
            modal = SugestaoModal(self.bot)
            await interaction.response.send_modal(modal)

        button.callback = button_callback

        view = View()
        view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)

class SugestaoModal(discord.ui.Modal, title="Compartilhe sua Sugestão"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    suggestion = discord.ui.TextInput(
        label="Qual a sua sugestão?",
        max_length=500,
        required=True,
        placeholder="Digite sua sugestão aqui...",
        style=discord.TextStyle.paragraph,
        min_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(SUGGESTIONS_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Canal para sugestões não encontrado.", ephemeral=True)
            return

        suggestion_embed = discord.Embed(
            title="💡 **Nova Sugestão Recebida!**",
            description=f"`{self.suggestion.value}`",
            color=0x740A92
        )
        suggestion_embed.add_field(name="📨 Enviado por", value=interaction.user.mention, inline=False)
        suggestion_embed.set_footer(text="Sua opinião é importante para nós!")
        suggestion_embed.set_thumbnail(url=THUMBNAIL_URL)

        view = VotingView(message_id=None, bot=self.bot)

        try:
            message = await channel.send(embed=suggestion_embed, view=view)

            # Armazenar o ID da mensagem
            view.message_id = message.id

            # Inicializar a contagem de votos
            votes[message.id] = {"yes": [], "no": []}

        except Exception as e:
            await interaction.response.send_message(f"Ocorreu um erro ao processar a sugestão: {e}", ephemeral=True)

        await interaction.response.send_message("Sua sugestão foi enviada com sucesso!", ephemeral=True)

class VotingView(View):
    def __init__(self, message_id, bot):
        super().__init__()
        self.message_id = message_id
        self.bot = bot

    @discord.ui.button(label="👍 A Favor", style=discord.ButtonStyle.success)
    async def vote_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "yes")

    @discord.ui.button(label="👎 Contra", style=discord.ButtonStyle.danger)
    async def vote_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register_vote(interaction, "no")

    @discord.ui.button(label="👀 Ver Votos", style=discord.ButtonStyle.secondary)
    async def view_votes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.display_votes(interaction)

    async def register_vote(self, interaction: discord.Interaction, vote_type: str):
        message_id = self.message_id
        user = interaction.user

        # Verifica se o usuário já votou
        if user.id in votes[message_id]["yes"] or user.id in votes[message_id]["no"]:
            await interaction.response.send_message("Você já votou nessa sugestão.", ephemeral=True)
            return

        # Registrar o voto
        votes[message_id][vote_type].append(user.id)

        # Atualizar a embed com a nova contagem de votos
        await self.update_votes(interaction.message)

        await interaction.response.send_message("Seu voto foi registrado com sucesso!", ephemeral=True)

    async def update_votes(self, message: discord.Message):
        message_id = self.message_id

        yes_count = len(votes.get(message_id, {}).get('yes', []))
        no_count = len(votes.get(message_id, {}).get('no', []))

        embed = message.embeds[0]
        embed.set_footer(text=f"👍 Aprovado: {yes_count} | 👎 Rejeitado: {no_count}")

        await message.edit(embed=embed)

    async def display_votes(self, interaction: discord.Interaction):
        message_id = self.message_id

        yes_voters = [self.bot.get_user(user_id).mention for user_id in votes.get(message_id, {}).get('yes', [])]
        no_voters = [self.bot.get_user(user_id).mention for user_id in votes.get(message_id, {}).get('no', [])]

        voters_embed = discord.Embed(
            title="🔍 **Detalhes dos Votos**",
            color=0x00aaff
        )
        voters_embed.add_field(
            name="👍 Votos a Favor",
            value="\n".join(yes_voters) if yes_voters else "Nenhum voto a favor.",
            inline=False
        )
        voters_embed.add_field(
            name="👎 Votos Contra",
            value="\n".join(no_voters) if no_voters else "Nenhum voto contra.",
            inline=False
        )
        voters_embed.set_footer(text="Essa informação é visível apenas para você.")

        await interaction.response.send_message(embed=voters_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Sugestao(bot))
