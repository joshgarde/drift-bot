import asyncio
import csv
import os
from pathlib import Path
from random import choice

from dotenv import load_dotenv
import nextcord
from nextcord.ext import commands
from pytube import YouTube

load_dotenv()

song_list = list(csv.DictReader(open('eurobeat.csv')))
image_list = list(Path('images').iterdir())
bot = commands.Bot('!')

@bot.event
async def on_ready():
    game = nextcord.Game("Running in the '90s")
    await bot.change_presence(activity=game)

    print(f'User: {bot.user.name}#{bot.user.discriminator}')
    print(f'OAuth URL: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=3214336&redirect_uri=https%3A%2F%2Fwww.duckduckgo.com%2F&scope=bot')
    print('Guilds:')
    print('\n'.join([f'  - {guild.name}' for guild in bot.guilds]))


@bot.command()
async def eurobeat(ctx):
    if ctx.author.bot:
        return

    voice_state = ctx.author.voice
    if voice_state == None or voice_state.channel == None:
        await ctx.reply('You\'re not currently connected to a voice channel')
        return

    voice_channel = voice_state.channel
    voice_client = await voice_channel.connect()
    print(f'Now connected to #{voice_channel.name} on "{voice_channel.guild.name}"')

    asyncio.get_event_loop().create_task(__play_next(ctx))

@bot.command()
async def drift(ctx):
    if ctx.author.bot:
        return

    voice_client = ctx.voice_client
    if voice_client == None:
        await ctx.reply('Not connected to any voice channels :(')
        return

    voice_client.stop()

    file = nextcord.File(open(choice(image_list), 'rb'))
    await ctx.reply(file=file)

@bot.command()
async def stopthemusic(ctx):
    if ctx.author.bot:
        return

    if ctx.voice_client == None:
        return

    await ctx.voice_client.disconnect()
    await ctx.reply('https://www.youtube.com/watch?v=sFODclG8mBY')


async def __play_next(ctx):
    if ctx.voice_client == None or not ctx.voice_client.is_connected():
        return

    voice_client = ctx.voice_client
    voice_channel = voice_client.channel

    random_eurobeat = choice(song_list)
    title = random_eurobeat['title']
    artist = random_eurobeat['artist']
    url = random_eurobeat['url']

    stream = YouTube(url).streams \
        .filter(only_audio=True).order_by('abr').desc().first()
    download_path = Path('downloads').joinpath(stream.default_filename)

    # Jank caching mechanism
    if not download_path.is_file():
        print(f'Starting download: {download_path}')
        stream.download('downloads')
        print(f'Finished download: {download_path}')
    else:
        print(f'Cached file found: {download_path}')

    _loop = asyncio.get_event_loop()

    def on_after(error):
        _loop.create_task(__play_next(ctx))

    audio_source = await nextcord.FFmpegOpusAudio.from_probe(download_path)
    voice_client.play(audio_source, after=on_after)

    print(f'Playing "{title}" in #{voice_channel.name} on "{voice_channel.guild.name}"')
    await ctx.send(f'Now playing: {title} by {artist}\n{url}')

if __name__ == '__main__':
    bot.run(os.environ['TOKEN'])
