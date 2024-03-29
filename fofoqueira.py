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
import logging

logging.basicConfig(level=logging.DEBUG)

CACHE_TIMEOUT = 60  # Tempo limite do cache em segundos
stream_data_cache = {} 

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
# -----------------------------------

# < ------ sala compartilhada ------ >
arkServer = db['ark']
# -----------------------------------

# Remover Help padrão
client.remove_command("help")

def is_running_on_heroku():
    result = 'DYNO' in os.environ
    print(f"Running on Heroku: {result}")
    return result

@client.event
async def on_ready():
    # enviar_mensagem_bazar.start()
    check_stream.start()
    check_servidor_ark.start()

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
      "incomingMessage": f"O(a) {valor} está online. Assista em https://www.twitch.tv/{valor}",
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


# @tasks.loop(minutes=300.0)
# async def enviar_mensagem_bazar():
#     running_on_heroku = is_running_on_heroku()

#     vendas_cursor = bazar.find()

#     lista_de_vendas = []
#     for venda in vendas_cursor:
#         lista_de_vendas.extend(venda["listaDeVendas"])

#     target_servers = []
#     if not running_on_heroku:
#         target_servers.append("767037529966641173")
#     else:
#         target_servers = [guild.id for guild in client.guilds]

#     for server_id in target_servers:
#         if not lista_de_vendas:
#             response = random.choice(
#                 [
#                     "**Vocês tão sendo leigos! Coloca um negócio a venda ae!!!**",
#                     "**Não tem nada a venda? Como pode...**",
#                     "**Eu só queria comprar uma merdinha...**",
#                     "**Anuncia ae, esse bazar ta com teia de aranha já!**",
#                     "**Nenhum corno ou corna anunciou ainda!!! Irei fechar essa merda.**",
#                     "**Anuncia bb que eu to carente já**",
#                     "**Anuncie aqui, bota tudo, lá ele!!!**",
#                     "**Extra extra extra, zero pessoas enganadas, vão anunciar não?**",
#                 ]
#             )
#             await channel.send(response)
#         else:
#             for venda in lista_de_vendas:
#                 channel = discord.utils.get(
#                     client.get_all_channels(), name="bazar-do-leigo"
#                 )
#                 embed = discord.Embed(
#                     title="Items a Venda",
#                     url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg",
#                     description=random.choice(
#                         [
#                             "Você não vai querer perder essa oportunidade! ",
#                             "Corre lá! Mas lembre-se que você não é parça do Neymar...",
#                             "Não deixe essa oportunidade passar! ",
#                             "Não fique de fora! Aproveite pra dar o golpe! ",
#                             "Não perca essa chance! Vai ser como roubar doce de criança. ",
#                             "Não perca essa oportunidade única de fazer merda! ",
#                             "The Bazar da fofoqueira venda e compre já never ends.",
#                         ]
#                     ),
#                     color=0xFF0000,
#                 )
#                 embed.set_author(
#                     name="Leigo: " + venda["author"],
#                     icon_url="https://d1fdloi71mui9q.cloudfront.net/2fJzNj9WQI6A26GTyqFa_w1c5QzIiE78smV4h",
#                 )
#                 embed.set_thumbnail(url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg")
#                 embed.add_field(name="Produto:", value=venda["produto"], inline=True)
#                 embed.add_field(name="Preço:", value="R$ " + str(venda["valor"]), inline=True)
#                 await channel.send(embed=embed)


# @client.event
# async def on_ready():
#     enviar_mensagem_bazar.start()
#     check_stream.start()

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

# <------------------------------------ ARK --------------------------------->

@client.command()
async def add_channel_server_ark(ctx, valor: str):
    # if ctx.author.id != ctx.guild.owner_id:
    #     await ctx.send("Você não tem permissão para usar esse comando.")
    #     return

    server_id = ctx.guild.id

    arkServer.update_one({"serverId": str(server_id)}, {"$addToSet": {"serversArk": {
      "ip": valor,
      "status": False,
      "upMessage": "O servidor está online",
      "downMessage": "O servidor está offline",
      "name": "",
      "everyone": False
    }}})

    await ctx.send(f"Novo servidor de ark, adicionado para notificação de online/offline!")

async def sendMessageNotificationServer(msg, servidorId):
    for guild in client.guilds:
        if str(guild.id) == str(servidorId):
            channelArk = "servidores"
            num_docs = arkServer.count_documents({'serverId': str(guild.id)})
            if (num_docs > 0):
                channelArk = arkServer.find_one({'serverId': str(guild.id)})["channelName"]
            for channel in guild.text_channels:
                if handleString(channel.name).upper() == handleString(str(channelArk)).upper():
                    await channel.send(msg)

@tasks.loop(seconds=6)
async def check_servidor_ark():
    servers = arkServer.find()
    data = await get_server_ark()
    for server in servers:
        serversArk = server["serversArk"]
        for ark in serversArk:
            ipBase = ark["ip"]
            statusBase = ark["status"]
            everyone = ark["everyone"]
            for info in data:
                ip = info["attributes"]["ip"]
                port = info["attributes"]["port"]
                status = info["attributes"]["status"]
                name = info["attributes"]["name"]
                addresss = ip + ":" + str(port)
                if ipBase == addresss and str(status) != str(statusBase):
                    arkServer.update_one(
                        {"serverId": str(server["serverId"]),
                         "serversArk": {"$elemMatch": {"ip": ipBase}}},{"$set": {"serversArk.$.status": status, "serversArk.$.name": name}})
                    upMessage = ""
                    downMessage = ""
                    if everyone:
                        upMessage = f'@everyone\n'
                        downMessage = f'@everyone\n'
                    upMessage = upMessage + f"Servidor de nome: {name} está online!\n"
                    downMessage = downMessage + f"Servidor de nome: {name} está offline!\n"
                    upMessage = upMessage + ark["upMessage"]
                    downMessage = downMessage + ark["downMessage"]
                    if status == "online":
                        print(upMessage)
                        await sendMessageNotificationServer(upMessage, server["serverId"])
                    else:
                        print(downMessage)
                        await sendMessageNotificationServer(downMessage, server["serverId"])


async def get_server_ark():
    try:
        url = 'https://api.battlemetrics.com/servers'
        params = {'filter[game]': 'ark', "page[size]": 100 , 'fields[server]': 'name,ip,port,status'}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return data['data']
    except Exception as e:
        print(f"Ocorreu um erro na request da Twitch: {e}")
    return None

# ----------------------------------------------------------------------------

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

@tasks.loop(seconds=10)
async def check_stream():
    async with aiohttp.ClientSession(headers={"Client-ID": client_id_twitch, "Authorization": f"Bearer {token_twitch}"}) as session:
        try:
            servers = twitchChannel.find()
        except Exception as e:
            logging.exception("Error fetching servers from the database")
            return
        for server in servers:
            # if not is_running_on_heroku() and server["servidorId"] != "767037529966641173":
            #     continue
            try:
                streamers_for_channel = server["canais"]
            except KeyError:
                logging.warning(f"Server {server} does not have the key 'canais'")
                continue
            if streamers_for_channel is not None:
                for streamer in streamers_for_channel:
                    streamer_name = streamer["login"]
                    streamer_status = streamer["status"]
                    try:
                        streamer_data = await get_stream_data(session, streamer_name)
                    except Exception as e:
                        logging.exception(f"Error getting stream data for {streamer_name}")
                        continue
                    if streamer_data is not None:
                        streamer_current_status = streamer_data["is_live"]
                        if str(streamer_status) != str(streamer_current_status):
                            twitchChannel.update_one({"servidorId": server["servidorId"], "canais": {"$elemMatch": {"login": streamer_name}}}, {"$set": {"canais.$.status": streamer_current_status}})
                            incomingMessage = ""
                            mensagemSaida = ""
                            streamer_msg_for_all = streamer["paraTodos"]
                            if streamer_msg_for_all:
                                incomingMessage = f'@everyone\n'
                                mensagemSaida = f'@everyone\n'
                            incomingMessage = incomingMessage + streamer["mensagemEntrada"]
                            mensagemSaida = mensagemSaida + streamer["mensagemSaida"]
                            if streamer_current_status:
                                gameName = await get_game_name(session, streamer_name)
                                incomingMessage = incomingMessage + "\nJogo: " + gameName
                                print(incomingMessage)
                                try:
                                    await sendMessageNotificationTwitch(incomingMessage, server["servidorId"])
                                except Exception as e:
                                    logging.exception(f"Error sending message for server {server['servidorId']}")
                                    continue
                            else:
                                await sendMessageNotificationTwitch(mensagemSaida, server["servidorId"])


async def get_stream_data(session, user):
    current_time = time.time()

    # Verifica se os dados do streamer estão no cache e se ainda são válidos
    if user in stream_data_cache and current_time - stream_data_cache[user]['timestamp'] < CACHE_TIMEOUT:
        return stream_data_cache[user]['data']

    url = f"https://api.twitch.tv/helix/search/channels?query={user}"
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            for item in data["data"]:
                if item["broadcaster_login"] == user:
                    # Armazena os dados do streamer no cache e registra o horário atual
                    stream_data_cache[user] = {'data': item, 'timestamp': current_time}
                    return item
    except aiohttp.ClientError as e:
        logging.exception(f"Error in Twitch request: {e}")

    return None

async def get_game_name(session, channel_name):
    url = f"https://api.twitch.tv/helix/streams?user_login={channel_name}"
    async with session.get(url) as response:
            data = await response.json()
    if data["data"]:
        return data["data"][0]["game_name"]
    return None

def handleString(palavra):
    texto_sem_traco = re.sub(r'[-_]', '', palavra)
    texto_sem_emojis = remover_emojis(texto_sem_traco)
    texto_sem_especiais = re.sub(r'[^\w\s]', '', texto_sem_emojis)
    texto_sem_acento = unidecode(texto_sem_especiais)
    texto_sem_acento = texto_sem_acento.replace("ç", "c").replace("Ç", "c")
    return texto_sem_acento

async def sendMessageNotificationTwitch(msg, servidorId):
    for guild in client.guilds:
        if str(guild.id) == str(servidorId):
            channelTwitch = "LIVES"
            try:
                num_docs = twitchChannel.count_documents({'servidorId': str(guild.id)})
            except Exception as e:
                logging.exception(f"Error counting documents for server {guild.id}")
                return
            if (num_docs > 0):
                try:
                    channelTwitch = twitchChannel.find_one({'servidorId': str(guild.id)})["nomeCanal"]
                except KeyError:
                    logging.warning(f"Server {guild.id} does not have the key 'nomeCanal'")
                except Exception as e:
                    logging.exception(f"Error finding server {guild.id} in the database")
                    return
            print(channelTwitch)
            for channel in guild.text_channels:
                if handleString(channel.name).upper() == handleString(str(channelTwitch)).upper():
                    try:
                        await channel.send(msg)
                    except Exception as e:
                        logging.exception(f"Error sending message to channel {channel.name}")
                        return


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
