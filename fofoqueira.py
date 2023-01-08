import discord
from discord.ext import commands
from decouple import config
import requests
import random
import json
import re
from datetime import datetime

client = commands.Bot(command_prefix='.', intents=discord.Intents.all())

flood_limit = 5
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
@client.event
async def on_voice_state_update(member, before, after):
  now = datetime.utcnow()
  if before.channel is None and after.channel is not None:
    if member.id in voice_join_times:
      time_since_last_join = now - voice_join_times[member.id]
      if time_since_last_join.seconds < flood_limit:
        await member.send('Você está entrando no canal de voz com uma frequência maior do que o permitido. Por favor, aguarde alguns segundos antes de entrar novamente.')
        await member.edit(nick="Flodador")
        return
    else:
      await after.channel.send(f'{member.mention} entrou no canal {remover_emojis(after.channel.name)}', tts=True)
    voice_join_times[member.id] = now
  elif before.channel is not None and after.channel is None:
    await before.channel.send(f'{member.mention} saiu do canal {remover_emojis(before.channel.name)}', tts=True)

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

TOKEN = config("TOKEN")
client.run(TOKEN)




