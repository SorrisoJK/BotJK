import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os
import hashlib
import uuid
from datetime import datetime

# IDs dos canais
COMMAND_CHANNEL_ID = 1242129028425715742  # Substitua pelo ID do canal onde o comando deve ser usado
EMBED_CHANNEL_ID = 1242129022717001808    # Substitua pelo ID do canal onde a embed deve ser postada
INFO_CHANNEL_ID = 1242129028425715742     # Substitua pelo ID do canal onde as informações da indicação serão enviadas

# IDs dos cargos permitidos para usar o comando
ALLOWED_ROLE_IDS = [
    1242127891857149992,  # Substitua pelos IDs dos cargos permitidos
    222222222222222222,
    333333333333333333,
    # Adicione mais IDs de cargos conforme necessário
]

# URL da imagem padrão para a embed
DEFAULT_IMAGE_URL = 'https://media.discordapp.net/attachments/998288964156923904/1265169352672415786/Logo_Animada_GIF_15_FPS_mmb.gif?ex=66b5a047&is=66b44ec7&hm=ed3dcbeec3cb0fb1346496629e8e37f022aa9d329dcc0f9d05bb41acff65fc50&=&width=350&height=350'

def load_indicated_users():
    if os.path.exists('indicated_users.json'):
        with open('indicated_users.json', 'r') as f:
            return json.load(f)
    return {}

def save_indicated_users(indicated_users):
    with open('indicated_users.json', 'w') as f:
        json.dump(indicated_users, f)

def load_indication_log():
    if os.path.exists('indication_log.json'):
        with open('indication_log.json', 'r') as f:
            return json.load(f)
    return {}

def save_indication_log(indication_log):
    with open('indication_log.json', 'w') as f:
        json.dump(indication_log, f)

def generate_short_id():
    uid = str(uuid.uuid4())
    hash_object = hashlib.md5(uid.encode())
    short_id = hash_object.hexdigest()[:8]
    return short_id

class Indicacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog 'indicacao' carregado com sucesso.")

    @discord.app_commands.command(name="indicar", description="Indique um jogador e as cidades onde ele jogou.")
    async def indicar(self, interaction: discord.Interaction, user: discord.Member, cidades: str):
        if interaction.channel.id != COMMAND_CHANNEL_ID:
            await interaction.response.send_message(f"Este comando só pode ser usado no canal <#{COMMAND_CHANNEL_ID}>.", ephemeral=True)
            return

        has_role = any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        indicated_users = load_indicated_users()
        indication_id = generate_short_id()

        if str(user.id) in indicated_users:
            await interaction.response.send_message(f"{user.mention} já foi indicado anteriormente.", ephemeral=True)
            return

        guild = interaction.guild
        icon_url = f"https://cdn.discordapp.com/icons/{guild.id}/{guild.icon}.png" if guild.icon else DEFAULT_IMAGE_URL

        embed = discord.Embed(title="`🎁 INDICAÇÃO DE MEMBRO`", color=0x7289da)
        embed.add_field(name="Informações da Indicação", value=f"Membro indicado: {user.mention}\nIndicador do membro: {interaction.user.mention}\nCidades do indicado: `{cidades}`\nID da indicação: `{indication_id}`", inline=False)
        embed.set_thumbnail(url=icon_url)

        approve_button = Button(label="Aprovar indicação", style=discord.ButtonStyle.secondary)
        reject_button = Button(label="Reprovar indicação", style=discord.ButtonStyle.danger)

        async def approve(interaction: discord.Interaction):
            role = discord.utils.get(interaction.guild.roles, name="・Cidadão")
            if role:
                await user.add_roles(role)
                await interaction.response.send_message(f"{user.mention} foi aprovado e recebeu o cargo {role.name}.", ephemeral=True)

                approved_embed = discord.Embed(title="Indicação Aprovada", color=0x00ff00)
                approved_embed.add_field(name="Informações da Indicação", value=f"Membro indicado: {user.mention}\nIndicador do membro: {interaction.user.mention}\nCidades do indicado: `{cidades}`\nID da indicação: `{indication_id}`", inline=False)
                approved_embed.set_thumbnail(url=DEFAULT_IMAGE_URL)

                approved_button = Button(label="Indicação Aprovada", style=discord.ButtonStyle.secondary, disabled=True)
                view = View()
                view.add_item(approved_button)

                await message.edit(embed=approved_embed, view=view)

                indication_log = load_indication_log()
                if indication_id not in indication_log:
                    indication_log[indication_id] = {
                        'status': 'Aprovado',
                        'approved_by': str(interaction.user.id),
                        'date': datetime.now().isoformat(),
                        'indicator': str(interaction.user.id),
                        'indicated': str(user.id)
                    }
                    save_indication_log(indication_log)

                indicated_users[str(user.id)] = user.name
                save_indicated_users(indicated_users)
            else:
                await interaction.response.send_message("Cargo não encontrado.", ephemeral=True)
        
        async def reject(interaction: discord.Interaction):
            await interaction.response.send_message(f"A indicação de {user.mention} foi recusada.", ephemeral=True)

            rejected_embed = discord.Embed(title="Indicação Reprovada", color=0xff0000)
            rejected_embed.add_field(name="Informações da Indicação", value=f"Membro indicado: {user.mention}\nIndicador do membro: {interaction.user.mention}\nCidades do indicado: `{cidades}`\nID da indicação: `{indication_id}`", inline=False)
            rejected_embed.set_thumbnail(url=DEFAULT_IMAGE_URL)

            rejected_button = Button(label="Indicação Reprovada", style=discord.ButtonStyle.danger, disabled=True)
            view = View()
            view.add_item(rejected_button)

            await message.edit(embed=rejected_embed, view=view)

            indication_log = load_indication_log()
            if indication_id not in indication_log:
                indication_log[indication_id] = {
                    'status': 'Reprovado',
                    'approved_by': str(interaction.user.id),
                    'date': datetime.now().isoformat(),
                    'indicator': str(interaction.user.id),
                    'indicated': str(user.id)
                }
                save_indication_log(indication_log)

            indicated_users[str(user.id)] = user.name
            save_indicated_users(indicated_users)

        approve_button.callback = approve
        reject_button.callback = reject

        view = View()
        view.add_item(approve_button)
        view.add_item(reject_button)

        embed_channel = self.bot.get_channel(EMBED_CHANNEL_ID)
        if embed_channel:
            message = await embed_channel.send(embed=embed, view=view)
            await interaction.response.send_message(
                f"✅ **Indicação criada com sucesso!**\n\n"
                f"Obrigado por indicar um membro! 🙌\n"
                f"Aguarde enquanto nossa equipe revisa sua indicação.\n\n"
                f"📍 **Acompanhe a indicação**: <#{EMBED_CHANNEL_ID}>\n"
                f"**Código da Indicação:** `{indication_id}`",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("Canal de embed não encontrado.", ephemeral=True)

    @discord.app_commands.command(name="cdindicacao", description="Consulta informações de uma indicação pelo código.")
    async def cdindicacao(self, interaction: discord.Interaction, codigo: str):
        if interaction.channel.id != INFO_CHANNEL_ID:
            await interaction.response.send_message(f"Este comando só pode ser usado no canal <#{INFO_CHANNEL_ID}>.", ephemeral=True)
            return

        indication_log = load_indication_log()

        if codigo not in indication_log:
            await interaction.response.send_message("Código de indicação não encontrado.", ephemeral=True)
            return

        log_entry = indication_log[codigo]
        indicator_id = log_entry['indicator']
        indicated_id = log_entry['indicated']
        approved_by_id = log_entry.get('approved_by', 'Desconhecido')

        guild = interaction.guild
        indicator = guild.get_member(int(indicator_id))
        indicated = guild.get_member(int(indicated_id))
        approved_by = guild.get_member(int(approved_by_id)) if approved_by_id != 'Desconhecido' else None

        indications = list(indication_log.values())
        total_indications = len([i for i in indications if i['indicator'] == indicator_id])
        approved_count = len([i for i in indications if i['indicator'] == indicator_id and i['status'] == 'Aprovado'])
        rejected_count = len([i for i in indications if i['indicator'] == indicator_id and i['status'] == 'Reprovado'])

        embed = discord.Embed(title="`📊 INFORMAÇÕES DA INDICAÇÃO`", color=0x7289da)
        embed.add_field(name="Código da Indicação", value=codigo, inline=False)
        embed.add_field(name="Indicador", value=indicator.mention if indicator else "Desconhecido", inline=False)
        embed.add_field(name="Membro Indicado", value=indicated.mention if indicated else "Desconhecido", inline=False)
        embed.add_field(name="Aprovado por", value=approved_by.mention if approved_by else "Desconhecido", inline=False)
        embed.add_field(name="Data da Indicação", value=log_entry['date'], inline=False)
        embed.add_field(name="Status", value=log_entry['status'], inline=False)
        embed.add_field(name="Estatísticas do Indicador", value=f"Total de indicações: {total_indications}\nIndicações aprovadas: {approved_count}\nIndicações reprovadas: {rejected_count}", inline=False)
        embed.set_thumbnail(url=DEFAULT_IMAGE_URL)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Indicacao(bot))
