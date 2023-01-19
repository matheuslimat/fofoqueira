import discord
from discord.ext import commands, tasks
from decouple import config
import requests
import random
import json
import re
from datetime import datetime
import asyncio
import time

client = commands.Bot(command_prefix='f!', intents=discord.Intents.all())

flood_limit = 5
voice_join_times = {}
lista_de_vendas = []

# Remover Help padrão
client.remove_command('help')

@tasks.loop(minutes=59.0)
async def enviar_mensagem_bazar():
    channel = discord.utils.get(client.get_all_channels(), name='bazar-do-leigo') # Substitua 'channel-name' pelo nome do canal
    response = ""
    for venda in lista_de_vendas:
        embed=discord.Embed(title="Items a Venda", url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg", description=random.choice(["Você não vai querer perder essa oportunidade! ", "Corre lá! Mas lembre-se que você não é parça do Neymar...", "Não deixe essa oportunidade passar! ","Não fique de fora! Aproveite pra dar o golpe! ","Não perca essa chance! Vai ser como roubar doce de criança. ","Não perca essa oportunidade única de fazer merda! "]), color=0xff0000)
        embed.set_author(name="Leigo: " + venda["author"], icon_url="https://d1fdloi71mui9q.cloudfront.net/2fJzNj9WQI6A26GTyqFa_w1c5QzIiE78smV4h")
        embed.set_thumbnail(url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg")
        embed.add_field(name="Produto:", value=venda["produto"], inline=True)
        embed.add_field(name="Preço:", value="R$ " + str(venda["valor"]), inline=True)
        await channel.send(embed=embed)

    if (len(lista_de_vendas) == 0):
      response = random.choice(["**Vocês tão sendo leigos! Coloca um negócio a venda ae!!!**", "**Não tem nada a venda? Como pode...**", "**Eu só queria comprar uma merdinha...**","**Anuncia ae, esse bazar ta com teia de aranha já!**","**Nenhum corno ou corna anunciou ainda!!! Irei fechar essa merda.**"])
      await channel.send(response)

@client.event
async def on_ready():
    enviar_mensagem_bazar.start()

@client.command()
async def vender(ctx, valor: float, pix: str, *,produto: str):
  author = ctx.message.author

  embed=discord.Embed(title="Produto", url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg", description=random.choice(["Você não vai querer perder essa oportunidade! ", "Corre lá! Mas lembre-se que você não é parça do Neymar...", "Não deixe essa oportunidade passar! ","Não fique de fora! Aproveite pra dar o golpe! ","Não perca essa chance! Vai ser como roubar doce de criança. ","Não perca essa oportunidade única de fazer merda! "]), color=0xff0000)
  embed.set_author(name="Leigo: " + str(author), icon_url="https://d1fdloi71mui9q.cloudfront.net/2fJzNj9WQI6A26GTyqFa_w1c5QzIiE78smV4h")
  embed.set_thumbnail(url="https://i.ytimg.com/vi/WAjjmrVwDrI/maxresdefault.jpg")
  embed.add_field(name="Produto:", value=produto, inline=True)
  embed.add_field(name="Preço:", value="R$ " + str(valor), inline=True)
  embed.add_field(name="Chave Pix:", value=pix, inline=True)
  venda = {'author': str(author), 'produto': produto, 'valor': valor , 'pix': pix, 'id' : len(lista_de_vendas) + 1}
  lista_de_vendas.append(venda)
  await ctx.send(embed=embed)

@client.command()
async def vendas(ctx):
  if not lista_de_vendas:
    await ctx.send('Não há vendas cadastradas')
    return
  response = '**Lista de vendas:**\n'
  for venda in lista_de_vendas:
    response += f'O produto de id {venda["id"]} e possui o nome {venda["produto"]} está por R$ {venda["valor"]}, o usuario ({venda["author"]} esta vendendo!)\n'
  await ctx.send(response)

@client.command()
async def pix(ctx, author: str):
    author = author.lower()
    for item in lista_de_vendas:
        if author in item["author"].lower():
            await ctx.send(f'O pix de {item["author"]} é: {item["pix"]}')
            await ctx.send(file=discord.File('assets/faz_o_pix.png'))
            return
    await ctx.send(f'Não há venda cadastrada com o author fornecido.')

@client.command()
async def remover_venda(ctx, valor: int):
  author = ctx.message.author
  for i, item in enumerate(lista_de_vendas):
    if item["id"] == valor:
      if author == item["author"]:
        del lista_de_vendas[i]
        await ctx.send(f'Venda removida com sucesso!')
        return
      else:
        await ctx.send(f'Você não é o author da venda!')
        return
  await ctx.send(f'Não há venda cadastrada com o id fornecido.') 

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
    await ctx.send(file=discord.File('assets/la_ele.png'))
    await show_commands(ctx.message)

async def show_commands(message):
  command_list = [command.name for command in client.commands]
  await message.channel.send(f'Comandos disponíveis: {", ".join(command_list)}')

# < --------------------------------- LOL ------------------------------------------------------>
@client.command()
async def lol(ctx):
  print("aquii")
  url = "https://league-of-legends-galore.p.rapidapi.com/api/getPlayerRank"

  nickName = ctx.message.content[5:]
  querystring = {"name":nickName,"region":"br"}

  headers = {
  	"X-RapidAPI-Key": "0104c4d9f6msh2256b7bef11422ep150493jsn3eb1ae970e48",
  	"X-RapidAPI-Host": "league-of-legends-galore.p.rapidapi.com"
  }

  response = requests.request("GET", url, headers=headers, params=querystring)
  user = response.json()[0]

  username = user['username']
  rank = user['rank']
  emoji = ''
  points = user['lp']
  winLossRation = user['winLossRatio']

  if 'Gold' in rank:
    emoji = '<:7052lolrank4gold:1062550558927491142>'
  elif 'Silver' in rank:
    emoji = '<:3360lolrank3silver:1062550562027098142>'
  elif 'Bronze' in rank:
    emoji = '<:3360lolrank2bronze:1062550555433644073>'
  elif 'Iron' in rank:
    emoji = '<:4133lolrank1iron:1062550564975677492>'
  elif 'Platinum' in rank:
    emoji = '<:4183lolrank5platinum:1062550553089019975>'
  elif 'Diamond' in rank:
    emoji = '<:5693lolrank6diamond:1062550551499386940>'
  elif 'GrandMaster' in rank:
    emoji = '<:8981lolrank8grandmaster:1062550543479873597>'  
  elif 'Master' in rank:
    emoji = '<:9431lolrank7master:1062550548768895117>' 
  elif 'Challenger' in rank:
    emoji = '<:8641lolrank9challenger:1062550547049218098>' 

  embed=discord.Embed(title="RANK DO LOL", description=random.choice(["Esse leigo pensa que sabe jogar essa merda...", "Isso é um noob triste.......................", "Só joga de luquixi........................."]), color=0x00d5ff)
  embed.set_thumbnail(url="https://static.dicionariodesimbolos.com.br/upload/2a/fe/significado-da-bandeira-lgbt-e-sua-historia-8_xl.png")
  embed.add_field(name="User:", value=username, inline=False)
  embed.add_field(name="Vitorias/Derrotas:", value=winLossRation, inline=False)
  embed.add_field(name="Pontos:", value=points, inline=False)
  embed.add_field(name="Rank:", value=emoji, inline=False)


  await ctx.message.channel.send(embed=embed)
  await ctx.send(file=discord.File('assets/lol_banner.png'))
  


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
      respostasSufix = [' lulas! ', ' mangos! ', ' pila! ', ' bufunfa! ', ' faz o pikxii! ']  
      respostaPrefix = random.choice(respostasPrefix)
      respostaSufix = random.choice(respostasSufix)  
      if price:
        await message.channel.send(f'- {respostaPrefix} {price:.2f} {respostaSufix}') 
      else:
        await message.channel.send(f'Não foi possível encontrar o preço de {nome_jogo}')
    else:
      await message.channel.send(f'Nem o perigo achou esse jogo!!! Acho que é free... {nome_jogo}')
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
