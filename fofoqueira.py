import discord
from discord.ext import commands
from decouple import config

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

# Substitua bot_token pelo token do seu bot
TOKEN = config("TOKEN")
client.run(TOKEN)


# client.run("MTA2MDQyMDUwNDM1NzQzNzUyMA.G8mHPV.vLhOiEAJRkDoPcSfBZx1GSEr-o_BjCSPt56xdk")
# await channel.send(f'{member.mention} saiu no canal {channel.name}', tts=True)
