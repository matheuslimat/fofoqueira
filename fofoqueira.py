import discord
from discord.ext import commands
from decouple import config
import requests
import random
import json

client = commands.Bot(command_prefix='.', intents=discord.Intents.all())

# client = discord.Client()

@client.event
async def on_message(message):
    # Verificar se a mensagem começa com ".join"
    if message.content.startswith(".fofoqueira"):
        # Verificar se o autor da mensagem está em um canal de voz
        if message.author.voice is not None:
            # Conectar o bot ao canal de voz do autor da mensagem
            await message.author.voice.channel.connect()
    if message.content.startswith('.preco'):
        # Obtenha o nome do jogo da mensagem
        nome_jogo = message.content[7:]
        # Chame a função obter_preco_jogo com o nome do jogo
        preco = obter_preco_jogo(nome_jogo)

        respostasPrefix = ['Essa porcaria custa ', 'Essa belezinha custa ', 'Esse jogo de doente custa ']
        respostasSufix = [' lulas! ', ' mangos! ', ' pila! ', ' bufunfa! ']

        respostaPrefix = random.choice(respostasPrefix)
        respostaSufix = random.choice(respostasSufix)

        # Verifique se a função retornou um preço válido
        if preco:
          # Envie o preço para o canal
          await message.channel.send(f'- {respostaPrefix} {preco:.2f} {respostaSufix}') 
        else:
          # Se a função retornou None, envie uma mensagem informando que o jogo não foi encontrado ou não possui um preço definido
          await message.channel.send(f'Não foi possível encontrar o preço de {nome_jogo}')

# <---------------------------------- TTS ------------------------------------------------------>
@client.event
async def on_voice_state_update(member, before, after):
    # Verificar se o membro acabou de entrar em um canal de voz
    if before.channel is None and after.channel is not None:
        # Enviar uma mensagem dizendo que o membro entrou no canal
        await after.channel.send(f'{member.mention} entrou no canal {after.channel.name}', tts=True)
    # Verificar se o membro acabou de sair de um canal de voz
    elif before.channel is not None and after.channel is None:
        # Enviar uma mensagem dizendo que o membro saiu do canal
        await before.channel.send(f'{member.mention} saiu do canal {before.channel.name}', tts=True)


# <---------------------------- PRECO DOS JOGOS STEAM ----------------------------------------->

def obter_preco_jogo(nome_jogo):
  # Substitua os espaços no nome do jogo por %20 para torná-lo compatível com a URL
  nome_jogo = nome_jogo.replace(' ', '%20')
  # Envie uma solicitação à API do Steam para pesquisar o jogo
  r = requests.get(f'https://store.steampowered.com/api/storesearch?cc=BR&l=portuguese&term={nome_jogo}')
  # Analise a resposta JSON
  data = json.loads(r.text)
  # Verifique se o jogo foi encontrado
  if data['total'] > 0:
    # Obtenha o primeiro resultado (já que estamos pesquisando por nome, isso deve ser o jogo correto)
    game = data['items'][0]
    # Verifique se o jogo tem um preço definido
    if 'price' in game:
      # Obtenha o preço em BRL
      price = game['price']['final'] / 100
      # Retorne o preço
      return price
    else:
      # Se o jogo não tiver um preço definido, retorne None
      return None
  else:
    # Se o jogo não foi encontrado, retorne None
    return None


# @client.command()
# async def preco(ctx, *, nome_jogo):

#     respostasPrefix = ['Essa porcaria custa ', 'Essa belezinha custa ', 'Esse jogo de doente custa ']
#     respostasSufix = [' lulas! ', ' mangos! ', ' pila! ', ' bufunfa! ']

#     respostaPrefix = random.choice(respostasPrefix)
#     respostaSufix = random.choice(respostasSufix)

#     # Obtém o preço do jogo
#     preco = obter_preco_jogo(nome_jogo)
#     # Envia uma mensagem para o canal de texto com o preço do jogo
#     await ctx.send(respostaPrefix + preco + respostaSufix)



# Substitua bot_token pelo token do seu bot
TOKEN = config("TOKEN")
client.run(TOKEN)
