import discord
from discord.ext import commands
from decouple import config
import requests
import random

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
    # Faz a requisição à API da Steam para obter o preço do jogo
    response = requests.get(f'https://store.steampowered.com/api/appdetails?appids={nome_jogo}')
    # Verifica se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Carrega os dados da resposta em formato JSON
        dados = response.json()
        # Verifica se o jogo foi encontrado
        if 'success' in dados and dados['success']:
            # Verifica se o jogo possui preço
            if 'price_overview' in dados['data'] and 'final' in dados['data']['price_overview']:
                # Retorna o preço final do jogo
                return dados['data']['price_overview']['final']
            else:
                # Retorna uma mensagem indicando que o jogo não possui preço
                return 'O jogo não possui preço'
        else:
            # Retorna uma mensagem indicando que o jogo não foi encontrado
            return 'Jogo não encontrado'
    else:
        # Retorna uma mensagem de erro
        return 'Erro ao obter preço do jogo'

@client.command()
async def preco(ctx, *, nome_jogo):

    respostasPrefix = ['Essa porcaria custa ', 'Essa belezinha custa ', 'Esse jogo de doente custa ']
    respostasSufix = [' lulas! ', ' mangos! ', ' pila! ', ' bufunfa! ']

    respostaPrefix = random.choice(respostasPrefix)
    respostaSufix = random.choice(respostasSufix)

    # Obtém o preço do jogo
    preco = obter_preco_jogo(nome_jogo)
    # Envia uma mensagem para o canal de texto com o preço do jogo
    await ctx.send(respostaPrefix + preco + respostasSufix)



# Substitua bot_token pelo token do seu bot
TOKEN = config("TOKEN")
client.run(TOKEN)
