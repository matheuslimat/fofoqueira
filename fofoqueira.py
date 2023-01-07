import discord
from discord.ext import commands
from decouple import config
import requests
import random
import json
import re

client = commands.Bot(command_prefix='.', intents=discord.Intents.all())
countInteractive = 0
lastNameInteractive = None
lastNameInteractiveLimite = 5

@client.event
async def on_message(message):
    if message.content.startswith(".fofoqueira"):
        if message.author.voice is not None:
            await message.author.voice.channel.connect()
    if message.content.startswith('.preco'):
        await obter_preco_jogo(message)
        await exibir_imagem(message)


# <---------------------------------- TTS ------------------------------------------------------>
@client.event
async def on_voice_state_update(member, before, after):
  entrou = before.channel is None and after.channel is not None
  saiu = before.channel is not None and after.channel is None

  if entrou or saiu:
      contador = {'entradas': 0, 'saidas': 0}
      periodo = 60
      hora_inicio = time.time()
      while time.time() - hora_inicio < periodo:
          usuarios_no_canal = after.channel.members
          if member in usuarios_no_canal:
              contador['entradas'] += 1
          else:
              contador['saidas'] += 1
          time.sleep(1)

      if contador['entradas'] + contador['saidas'] > 20:
        print(f"Flood detectado por {member.name} em {after.channel.name}!")
        await member.edit(nick="Flodador")
      else:
        if before.channel is None and after.channel is not None:
          await after.channel.send(f'{member.mention} entrou no canal {after.channel.name}', tts=True)
        elif before.channel is not None and after.channel is None:
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
    # Remove os emojis do nome do canal usando expressões regulares
    return re.sub(r'[^\w\s]', '', nome_canal)


async def exibir_imagem(message):
  # Obtenha o nome do jogo da mensagem
  nome_jogo = message.content[7:]
  # Substitua os espaços no nome do jogo por %20 para torná-lo compatível com a URL
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
