import discord
from discord.ext import commands
from decouple import config
import requests
import random
import json
import re
import datetime
import asyncio

client = commands.Bot(command_prefix='.', intents=discord.Intents.all())

flood_limit = 10
voice_join_times = {}

@client.event
async def on_message(message):
  if message.content.startswith(".fofoqueira"):
    if message.author.voice is not None:
      await message.author.voice.channel.connect()
    if message.content.startswith('.preco'):
      await obter_preco_jogo(message)
      await exibir_imagem(message)
  if message.author.top_role.name == "Sênior" and message.content == ".rollback-nicks":
    for member in message.guild.members:
      if member.nick is not None:
        apelido_revertido = member.nick[::-1]
        await member.edit(nick=apelido_revertido)

# <---------------------------------- TTS ------------------------------------------------------>
async def on_voice_state_update(member, before, after):
  now = datetime.utcnow()

  if before.channel is None and after.channel is not None:
    if member.id in voice_join_times:
      time_since_last_join = now - voice_join_times[member.id]
      if time_since_last_join.seconds < flood_limit:
        await member.send('Você está entrando no canal de voz com uma frequência maior do que o permitido. Por favor, aguarde alguns segundos antes de entrar novamente.')
        ##await member.edit(voice_channel=None)
        await member.set_nickname('Flodador')
        return
      else:
        await after.channel.send(f'{member.mention} entrou no canal {after.channel.name}', tts=True)
    voice_join_times[member.id] = now
  elif before.channel is not None and after.channel is None:
    del voice_join_times[member.id]
    await before.channel.send(f'{member.mention} saiu do canal {before.channel.name}', tts=True)

# <---------------------------- PRECO DOS JOGOS STEAM ----------------------------------------->
async def obter_preco_jogo(message):
  nome_jogo = message.content[7:]
  nome_jogo = nome_jogo.replace(' ', '%20')
  r = requests.get(f'https://store.steampowered.com/api/storesearch?cc=BR&l=portuguese&term={nome_jogo}')
  data = json.loads(r.text)
  if data['total'] > 0:
    game = data['items'][0]
    if 'price' in game:
      price = game['price']['final'] / 100

      respostasPrefix = ['Essa porcaria custa ', 'Essa belezinha custa ', 'Esse jogo de doente custa ']
      respostasSufix = [' lulas! ', ' mangos! ', ' pila! ', ' bufunfa! ']  
      respostaPrefix = random.choice(respostasPrefix)
      respostaSufix = random.choice(respostasSufix)  
      if price:
        await message.channel.send(f'- {respostaPrefix} {price:.2f} {respostaSufix}') 
      else:
        await message.channel.send(f'Não foi possível encontrar o preço de {nome_jogo}')
    else:
      return None
  else:
    return None

def remover_emojis(nome_canal):
    return re.sub(r'[^\w\s]', '', nome_canal)

async def exibir_imagem(message):
  nome_jogo = message.content[7:]
  nome_jogo = nome_jogo.replace(' ', '%20')
  r = requests.get(f'https://store.steampowered.com/api/storesearch?cc=BR&l=portuguese&term={nome_jogo}')
  data = json.loads(r.text)
  if data['total'] > 0:
      game = data['items'][0]
      url_imagem = game['tiny_image']
      await message.channel.send(url_imagem)
  else:
      await message.channel.send(f'O jogo {nome_jogo} não foi encontrado')


async def tarefa_agendada():
  await client.wait_until_ready()
  while not client.is_closed():
    # Execute a ação a cada 10 minutos (600 segundos)
    await asyncio.sleep(600)
    await atribuir_apelidos()

async def atribuir_apelidos(client):
  members = client.get_all_members()

  for member in members:
    guild_member = await client.fetch_member(member.guild.id, member.id)
    joined_at = guild_member.joined_at
    time_since_last_seen = datetime.utcnow() - joined_at

    if time_since_last_seen > datetime.timedelta(days=3) and time_since_last_seen < datetime.timedelta(weeks=1):
      nickname = 'Foragido'
    elif time_since_last_seen > datetime.timedelta(weeks=1) and time_since_last_seen < datetime.timedelta(weeks=3):
      nickname = 'Procurado pela Interpool'
    elif time_since_last_seen > datetime.timedelta(weeks=2) and time_since_last_seen < datetime.timedelta(weeks=4):
      nickname = 'Procurado pelo FBI'
    elif time_since_last_seen > datetime.timedelta(weeks=4):
      nickname = 'CPF cancelado'
    else:
      nickname = None

    await guild_member.set_nickname(nickname)

client.loop.create_task(tarefa_agendada(client))


TOKEN = config("TOKEN")
client.run(TOKEN)
