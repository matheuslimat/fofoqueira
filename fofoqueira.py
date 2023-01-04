import discord
from discord.ext import commands

client = commands.Bot(command_prefix='.', intents=discord.Intents.all())


@client.event
async def on_ready():
    print('Conectado ao Discord como', client.user)

@client.event
async def on_message(message):
    # verifique se o comando é para conectar o bot a um canal de voz
    if message.content.startswith('.join'):
        # obtenha o canal de voz mencionado no comando
        voice_channel = message.author.voice.channel
        # conecte o bot ao canal de voz
        await voice_channel.connect()

@client.event
async def on_voice_state_update(member, before, after):
    # Verifica se o usuário entrou em um canal de voz
    if before.channel is None and after.channel is not None:
        # Envia uma mensagem para o canal de texto com o nome do usuário
        await after.channel.send(f'{member.mention} entrou no canal {after.channel.name}', tts=True)
    else:
        await before.channel.send(f'{member.mention} saiu do canal {before.channel.name}', tts=True)



client.run("MzMwNDk3ODA1MDM2NjgzMjc2.GNrocN.7XHsxvSpdSmDuO9OlyeSu6th-1X5qM-fvTrjr8")
