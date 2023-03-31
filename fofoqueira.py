import discord
from discord.ext import commands, tasks
from decouple import config
import requests
import random
import json
import re
from datetime import datetime, timedelta
from discord.ext import tasks
from unidecode import unidecode
import pymongo
import time
import aiohttp
import asyncio
import os

client = commands.Bot(command_prefix="f!", intents=discord.Intents.all())

mongo_uri = config("URL_MONGODB")
token_twitch = config("TOKEN_TWITCH")
client_id_twitch = config("CLIENT_ID_TWITCH")

clientMongoDB = pymongo.MongoClient(mongo_uri)
db = clientMongoDB['fofoqueira']

twitchChannel = db['twitch_channel']
bazar = db['bazar']


flood_limit = 5
voice_join_times = {}
reminders = []
current_status = True

# < ------ sala compartilhada ------ >
shared_channel_name = "sala_compartilhada"
# ---------------- #

# Remover Help padrão
client.remove_command("help")

def check_machine_enviroment():
    return "DYNO" not in os.environ

@client.command()
async def change_twitch_notification(ctx, channel):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Você não tem permissão para usar esse comando.")
        return
    
    server_id = ctx.guild.id

    twitchChannel.update_one({'servidorId': str(server_id)}, {"$set": {'nomeCanal': channel, 'servidorId': str(server_id)}}, upsert=True)

    await ctx.send(f"Novo canal de notificação twitch, salvo!")



@client.command()
async def vender(ctx, valor: float, pix: str, *, produto: str):
    author = ctx.message.author

    embed = discord.Embed(
        title="Produto",
        url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg",
        description=random.choice(
            [
                "Você não vai querer perder essa oportunidade! ",
                "Corre lá! Mas lembre-se que você não é parça do Neymar...",
                "Não deixe essa oportunidade passar! ",
                "Não fique de fora! Aproveite pra dar o golpe! ",
                "Não perca essa chance! Vai ser como roubar doce de criança. ",
                "Não perca essa oportunidade única de fazer merda! ",
            ]
        ),
        color=0xFF0000,
    )
    embed.set_author(
        name="Leigo: " + str(author),
        icon_url="https://d1fdloi71mui9q.cloudfront.net/2fJzNj9WQI6A26GTyqFa_w1c5QzIiE78smV4h",
    )
    embed.set_thumbnail(url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg")
    embed.add_field(name="Produto:", value=produto, inline=True)
    embed.add_field(name="Preço:", value="R$ " + str(valor), inline=True)
    embed.add_field(name="Chave Pix:", value=pix, inline=True)
    venda = {
        "author": str(author),
        "produto": produto,
        "valor": valor,
        "pix": pix,
        "id": current_milli_time()
    }

    bazar.update_one({"servidorId": str(ctx.guild.id)}, {"$addToSet": {"listaDeVendas": venda}})
    await ctx.send(embed=embed)

def current_milli_time():
    return round(time.time() * 1000)

@client.command()
async def add_channel_twitch(ctx, valor: str):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Você não tem permissão para usar esse comando.")
        return
    
    server_id = ctx.guild.id

    twitchChannel.update_one({"servidorId": str(server_id)}, {"$addToSet": {"canais": {
      "login": valor,  # Corrigido aqui
      "status": False,
      "mensagemEntrada": f"O(a) {valor} está online. Assista em https://www.twitch.tv/{valor}",
      "mensagemSaida": f"O(a) {valor} está offline.",
      "paraTodos": False
    }}})

    await ctx.send(f"Novo streamer, salvo para notificação de lives!")



@client.command()
async def vendas(ctx):
    lista_de_vendas = bazar.find({'servidorId': str(ctx.guild.id)})["listaDeVendas"]
    if not lista_de_vendas:
        await ctx.send("Não há vendas cadastradas")
        return
    response = "**Lista de vendas:**\n"
    for venda in lista_de_vendas:
        response += f'O produto de id {venda["id"]} e possui o nome {venda["produto"]} está por R$ {venda["valor"]}, o usuario ({venda["author"]} esta vendendo!)\n'
    await ctx.send(response)


@client.command()
async def pix(ctx, author: str):
    author = author.lower()
    lista_de_vendas = bazar.find({'servidorId': str(ctx.guild.id)})["listaDeVendas"]
    for item in lista_de_vendas:
        if author in item["author"].lower():
            await ctx.send(f'O pix de {item["author"]} é: {item["pix"]}')
            await ctx.send(file=discord.File("assets/faz_o_pix.png"))
            return
    await ctx.send(f"Não há venda cadastrada com o author fornecido.")


@client.command()
async def remover_venda(ctx, valor: int):
    author = ctx.message.author
    lista_de_vendas = bazar.find()["listaDeVendas"]
    for i, item in enumerate(lista_de_vendas):
        if item["id"] == valor:
            if author == item["author"]:
                del lista_de_vendas[i]
                await ctx.send(f"Venda removida com sucesso!")
                return
            else:
                await ctx.send(f"Você não é o author da venda!")
                return
    await ctx.send(f"Não há venda cadastrada com o id fornecido.")


@client.command()
async def preco(ctx):
    await obter_preco_jogo(ctx.message)
    await exibir_imagem(ctx.message)


@client.command()
async def fofoqueira(ctx):
    if ctx.message.author.voice is not None:
        await ctx.message.author.voice.channel.connect()


@client.command()
async def help(ctx):
    await show_commands(ctx.message)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.channel.send("Parece que você não sabe me usar(UUUUiii)")
        await ctx.send(file=discord.File("assets/la_ele.png"))
        await show_commands(ctx.message)


async def show_commands(message):
    command_list = [command.name for command in client.commands]
    await message.channel.send(f'Comandos disponíveis: {", ".join(command_list)}')


# < --------------------------------- LOL ------------------------------------------------------>
@client.command()
async def lol(ctx):
    url = "https://league-of-legends-galore.p.rapidapi.com/api/getPlayerRank"

    nickName = ctx.message.content[5:]
    querystring = {"name": nickName, "region": "br"}

    headers = {
        "X-RapidAPI-Key": "0104c4d9f6msh2256b7bef11422ep150493jsn3eb1ae970e48",
        "X-RapidAPI-Host": "league-of-legends-galore.p.rapidapi.com",
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    user = response.json()[0]

    username = user["username"]
    rank = user["rank"]
    emoji = ""
    points = user["lp"]
    winLossRation = user["winLossRatio"]

    if "Gold" in rank:
        emoji = "<:7052lolrank4gold:1062550558927491142>"
    elif "Silver" in rank:
        emoji = "<:3360lolrank3silver:1062550562027098142>"
    elif "Bronze" in rank:
        emoji = "<:3360lolrank2bronze:1062550555433644073>"
    elif "Iron" in rank:
        emoji = "<:4133lolrank1iron:1062550564975677492>"
    elif "Platinum" in rank:
        emoji = "<:4183lolrank5platinum:1062550553089019975>"
    elif "Diamond" in rank:
        emoji = "<:5693lolrank6diamond:1062550551499386940>"
    elif "GrandMaster" in rank:
        emoji = "<:8981lolrank8grandmaster:1062550543479873597>"
    elif "Master" in rank:
        emoji = "<:9431lolrank7master:1062550548768895117>"
    elif "Challenger" in rank:
        emoji = "<:8641lolrank9challenger:1062550547049218098>"

    embed = discord.Embed(
        title="RANK DO LOL",
        description=random.choice(
            [
                "Esse leigo pensa que sabe jogar essa merda...",
                "Isso é um noob triste.......................",
                "Só joga de luquixi.........................",
            ]
        ),
        color=0x00D5FF,
    )
    embed.set_thumbnail(
        url="https://static.dicionariodesimbolos.com.br/upload/2a/fe/significado-da-bandeira-lgbt-e-sua-historia-8_xl.png"
    )
    embed.add_field(name="User:", value=username, inline=False)
    embed.add_field(name="Vitorias/Derrotas:", value=winLossRation, inline=False)
    embed.add_field(name="Pontos:", value=points, inline=False)
    embed.add_field(name="Rank:", value=emoji, inline=False)

    await ctx.message.channel.send(embed=embed)
    await ctx.send(file=discord.File("assets/lol_banner.png"))

@tasks.loop(minutes=300.0)
async def enviar_mensagem_bazar():
    vendas_cursor = bazar.find()

    lista_de_vendas = []
    for venda in vendas_cursor:
        lista_de_vendas.extend(venda["listaDeVendas"])

    if not lista_de_vendas:
        response = random.choice(
            [
                "**Vocês tão sendo leigos! Coloca um negócio a venda ae!!!**",
                "**Não tem nada a venda? Como pode...**",
                "**Eu só queria comprar uma merdinha...**",
                "**Anuncia ae, esse bazar ta com teia de aranha já!**",
                "**Nenhum corno ou corna anunciou ainda!!! Irei fechar essa merda.**",
                "**Anuncia bb que eu to carente já**",
                "**Anuncie aqui, bota tudo, lá ele!!!**",
                "**Extra extra extra, zero pessoas enganadas, vão anunciar não?**",
            ]
        )
        await channel.send(response)
    else:
        for venda in lista_de_vendas:
            channel = discord.utils.get(
                client.get_all_channels(), name="bazar-do-leigo"
            )  # Substitua 'channel-name' pelo nome do canal

            embed = discord.Embed(
                title="Items a Venda",
                url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg",
                description=random.choice(
                    [
                        "Você não vai querer perder essa oportunidade! ",
                        "Corre lá! Mas lembre-se que você não é parça do Neymar...",
                        "Não deixe essa oportunidade passar! ",
                        "Não fique de fora! Aproveite pra dar o golpe! ",
                        "Não perca essa chance! Vai ser como roubar doce de criança. ",
                        "Não perca essa oportunidade única de fazer merda! ",
                        "The Bazar da fofoqueira venda e compre já never ends.",
                    ]
                ),
                color=0xFF0000,
            )
            embed.set_author(
                name="Leigo: " + venda["author"],
                icon_url="https://d1fdloi71mui9q.cloudfront.net/2fJzNj9WQI6A26GTyqFa_w1c5QzIiE78smV4h",
            )
            embed.set_thumbnail(url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg")
            embed.add_field(name="Produto:", value=venda["produto"], inline=True)
            embed.add_field(name="Preço:", value="R$ " + str(venda["valor"]), inline=True)
            await channel.send(embed=embed)

        


@client.event
async def on_ready():
    enviar_mensagem_bazar.start()
    check_stream.start()

# <---------------------------------- TTS ------------------------------------------------------>
@client.event
async def on_voice_state_update(member, before, after):
    now = datetime.utcnow()
    if before.channel is None and after.channel is not None:
        if member.id in voice_join_times:
            time_since_last_join = now - voice_join_times[member.id]
            if time_since_last_join.seconds < flood_limit:
                await member.send(
                    "Você está entrando no canal de voz com uma frequência maior do que o permitido. Por favor, aguarde alguns segundos antes de entrar novamente."
                )
                await member.edit(nick="Flodador")
                return
        await after.channel.send(
            f"{member.mention} entrou no canal {remover_emojis(after.channel.name)}",
            tts=True,
        )
        voice_join_times[member.id] = now
    elif before.channel is not None and after.channel is None:
        await before.channel.send(
            f"{member.mention} saiu do canal {remover_emojis(before.channel.name)}",
            tts=True,
        )
        
# <---------------------------- PRECO DOS JOGOS STEAM ----------------------------------------->

@client.command()
async def avise(ctx):
    message = ctx.message
    args = message.content.split()
    game_name = " ".join(args[1:-1])
    target_price = float(args[-1])

    r = requests.get(
    f"https://store.steampowered.com/api/storesearch?cc=BR&l=portuguese&term={game_name}"
    )
    data = json.loads(r.text)

    found = False
    if data["total"] > 0:
        game = data["items"][0]
        if "price" in game:
            price = game["price"]["final"] / 100

            found = True

            if price <= target_price:
                await message.channel.send(f"**{game_name} já está custando R${price} agora!**")
            else:
                reminders.append({"user": message.author.name, "game": game_name, "price": target_price})
                await message.channel.send(f"**Caro {message.author.name}, quando {game_name} atingir R${target_price} irei avisar a você.**")

    if not found:
        await message.channel.send(f"**Não foi possível encontrar o jogo '{game_name}' na Steam.**")

# <---------------------------- Lodout Pedro ----------------------------------------->

@client.command()
async def lodout(ctx, author: str):
    if author == 'pedro':
        await ctx.send(f"https://cdn.discordapp.com/attachments/767037529966641175/1076944158587109486/image.png")
        await ctx.send(f"https://cdn.discordapp.com/attachments/767037529966641175/1076945030603866143/image.png")
        await ctx.send(f"https://cdn.discordapp.com/attachments/767037529966641175/1076945096534138960/image.png")
        await ctx.send(f"https://cdn.discordapp.com/attachments/767037529966641175/1076945215467823194/image.png")
        await ctx.send(f"https://cdn.discordapp.com/attachments/767037529966641175/1076945627491074119/image.png")
        await ctx.send(f"https://cdn.discordapp.com/attachments/767037529966641175/1076945684097417276/image.png")
        await ctx.send(f"https://cdn.discordapp.com/attachments/767037529966641175/1076945739684524072/image.png")
        await ctx.send(f"https://cdn.discordapp.com/attachments/767037529966641175/1076945783699558563/image.png")
    else:
        await ctx.send(f"**{author} Não cadastrou lodout! **")



@tasks.loop(minutes=59.0)
async def check_reminders():
    for reminder in reminders:
        r = requests.get(
        f"https://store.steampowered.com/api/storesearch?cc=BR&l=portuguese&term={reminder['game']}"
        )
        data = json.loads(r.text)
        if data["total"] > 0:
            game = data["items"][0]
            if "price" in game:
                price = game["price"]["final"] / 100
                if price <= reminder["price"]:
                    channel = client.get_channel('fofoqueira')
                    await channel.send(f"**{reminder['user']} pediu para lembrar: {reminder['game']} está custando R${price} agora!**")
                    reminders.remove(reminder)
                    break


async def obter_preco_jogo(message):
    nome_jogo = message.content[7:]
    nome_jogo = nome_jogo.replace(" ", "%20")
    r = requests.get(
        f"https://store.steampowered.com/api/storesearch?cc=BR&l=portuguese&term={nome_jogo}"
    )
    data = json.loads(r.text)
    if data["total"] > 0:
        game = data["items"][0]
        if "price" in game:
            price = game["price"]["final"] / 100

            respostasPrefix = [
                "Essa porcaria custa ",
                "Essa belezinha custa ",
                "Esse jogo de doente custa ",
            ]
            respostasSufix = [
                " lulas! ",
                " mangos! ",
                " pila! ",
                " bufunfa! ",
                " faz o pikxii! ",
            ]
            respostaPrefix = random.choice(respostasPrefix)
            respostaSufix = random.choice(respostasSufix)
            if price:
                await message.channel.send(
                    f"- {respostaPrefix} {price:.2f} {respostaSufix}"
                )
            else:
                await message.channel.send(
                    f"Não foi possível encontrar o preço de {nome_jogo}"
                )
        else:
            await message.channel.send(
                f"Nem o perigo achou esse jogo!!! Acho que é free... {nome_jogo}"
            )
    else:
        return None


def remover_emojis(nome_canal):
    return re.sub(r"[^\w\s]", "", nome_canal)


async def exibir_imagem(message):
    nome_jogo = message.content[7:]
    nome_jogo = nome_jogo.replace(" ", "%20")
    r = requests.get(
        f"https://store.steampowered.com/api/storesearch?cc=BR&l=portuguese&term={nome_jogo}"
    )
    data = json.loads(r.text)
    if data["total"] > 0:
        game = data["items"][0]
        url_imagem = game["tiny_image"]
        await message.channel.send(url_imagem)
    else:
        await message.channel.send(f"O jogo {nome_jogo} não foi encontrado")


# < ----------------------- Gratis EPIC --------------------->
async def check_epic_games():
    channel = discord.utils.get(
        client.get_all_channels(), name="jogo-gratis-ou-da-epic"
    )  # Substitua 'channel-name' pelo nome do canal
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=pt-BR&country=BR&allowCountries=BR"

    response = requests.get(url)
    data = json.loads(response.text)

    free_games = data["data"]["Catalog"]["searchStore"]["elements"]

    if free_games:
        for game in free_games:
            if(game["status"] == "ACTIVE"):
                title = game["title"]
                original_price = game["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
                discount_price = game["price"]["totalPrice"]["fmtPrice"]["discountPrice"]
                url_game = game["keyImages"][0]["url"]


                message = f"**Jogo baratos ou gratuitos disponível: ** {title} (Preço original: {original_price} | Preço com desconto: {discount_price}) - {url_game}"
                await channel.send(message)
    else:
        await channel.send("**Não há jogos baratos ou gratuitos disponíveis na Epic Games Store no momento.**")
# ----------------------------------------------------------------------------------------------------------------------------------------#
@tasks.loop(seconds=5)
async def check_stream():
    async with aiohttp.ClientSession(headers={"Client-ID": client_id_twitch, "Authorization": f"Bearer {token_twitch}"}) as session:
        servers = twitchChannel.find()
        for server in servers:
            streamers_for_channel = server["canais"]
            if streamers_for_channel is not None:
                for streamer in streamers_for_channel:
                    streamer_name = streamer["login"]
                    streamer_status = streamer["status"]
                    streamer_data = await get_stream_data(session, streamer_name)
                    if streamer_data is not None:
                        streamer_current_status = streamer_data["is_live"]
                        if streamer_status != streamer_current_status:
                            twitchChannel.update_one({"servidorId": server["servidorId"], "canais": {"$elemMatch": {"login": streamer_name}}}, {"$set": {"canais.$.status": streamer_current_status}})
                            mensagemEntrada = ""
                            mensagemSaida = ""
                            streamer_msg_for_all = streamer["paraTodos"]
                            if streamer_msg_for_all == True:
                                mensagemEntrada = f'@everyone\n'
                                mensagemSaida = f'@everyone\n'
                            mensagemEntrada = mensagemEntrada + streamer["mensagemEntrada"]
                            mensagemSaida = mensagemSaida + streamer["mensagemSaida"]
                            if (streamer_current_status == True):
                                await enviarMensagemNotificationTwitch(mensagemEntrada, server["servidorId"])
                            else:
                                await enviarMensagemNotificationTwitch(mensagemSaida, server["servidorId"])

async def get_stream_data(session, user):
    url = f"https://api.twitch.tv/helix/search/channels?query={user}"

    try:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            for item in data["data"]:
                if item["broadcaster_login"] == user:
                    return item
    except aiohttp.ClientError as e:
        print(f"Ocorreu um erro na request da Twitch: {e}")
    
    return None

def removeCaractere(palavra):
    texto_sem_traco = re.sub(r'[-_]', '', palavra)
    texto_sem_emojis = remover_emojis(texto_sem_traco)
    texto_sem_especiais = re.sub(r'[^\w\s]', '', texto_sem_emojis)
    texto_sem_acento = unidecode(texto_sem_especiais)
    texto_sem_acento = texto_sem_acento.replace("ç", "c").replace("Ç", "c")
    return texto_sem_acento

async def enviarMensagemNotificationTwitch(msg, servidorId):
    for guild in client.guilds:
        if str(guild.id) == str(servidorId):
            channelTwitch = "LIVES"
            num_docs = twitchChannel.count_documents({'servidorId': str(guild.id)})
            if (num_docs > 0):
                channelTwitch = twitchChannel.find_one({'servidorId': str(guild.id)})["nomeCanal"]
            print(channelTwitch)
            for channel in guild.text_channels:
                if removeCaractere(channel.name).upper() == removeCaractere(str(channelTwitch)).upper():
                    await channel.send(msg)

# < --------------------------------- SALA COMPARTILHADA ----------------------------------->

async def get_shared_channel(guild):
    for channel in guild.text_channels:
        if channel.name == shared_channel_name:
            return channel
    return None

async def create_shared_channel(guild):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    return await guild.create_text_channel(shared_channel_name, overwrites=overwrites)

@client.command(name="sala_compartilhada")
async def register_shared_channel(ctx):
    shared_channel = await get_shared_channel(ctx.guild)
    if shared_channel is None:
        await create_shared_channel(ctx.guild)
        await ctx.send("Canal compartilhado 'sala_compartilhada' criado com sucesso!")
    else:
        await ctx.send("O canal 'sala_compartilhada' já está cadastrado neste servidor.")

@client.event
async def on_message(message):

    if message.author.bot:
        return
    
    if message.author == client.user:
        await client.process_commands(message)
        return

    shared_channel = await get_shared_channel(message.guild)
    if message.channel == shared_channel:
        if message.content.startswith("f!"):
            await message.channel.send(f"{message.author.mention}, comandos não são permitidos neste canal.")
            return

        msg_content = f"**{message.author} (de {message.guild.name}):** {message.content}"
        for guild in client.guilds:
            if guild != message.guild:
                other_shared_channel = await get_shared_channel(guild)
                if other_shared_channel is not None:
                    await other_shared_channel.send(msg_content)
    elif message.content.startswith(client.command_prefix):
        await client.process_commands(message)

@client.command()
async def clean(ctx, channel_name: str):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Apenas o dono do servidor pode usar este comando.")
        return

    shared_channel = None
    for channel in ctx.guild.text_channels:
        if channel.name == channel_name:
            shared_channel = channel
            break

    if shared_channel is not None:
        await shared_channel.purge()
        await ctx.send(f"O canal '{channel_name}' foi limpo!")
    else:
        await ctx.send(f"O canal '{channel_name}' não foi encontrado!")

TOKEN = config("TOKEN")
client.run(TOKEN)
