import os
from dotenv import load_dotenv
from discord import Intents
from discord.ext import commands
import qbittorrentapi
import discord
from functions import *


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
QBT_HOST = os.getenv('QBT_HOST')
QBT_PORT = os.getenv('QBT_PORT')
QBT_USERNAME = os.getenv('QBT_USERNAME')
QBT_PASSWORD = os.getenv('QBT_PASSWORD')
QBT_API_KEY = os.getenv('QBT_API_KEY')


def validate_config():
    missing = []
    if not TOKEN:
        missing.append('DISCORD_TOKEN')
    if not QBT_HOST:
        missing.append('QBT_HOST')
    if not QBT_API_KEY:
        if not QBT_USERNAME:
            missing.append('QBT_USERNAME')
        if not QBT_PASSWORD:
            missing.append('QBT_PASSWORD')
    if missing:
        raise SystemExit('Missing required environment variables: ' + ', '.join(missing))

intents = Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.hybrid_command()
async def downloading(ctx: commands.Context):
    MovieList = []
    TVList = []
    OtherList = []
    count=0
    for torrent in qbt_client.torrents.info.active():
        if torrent.category == 'radarr':
            count = count+1
            TempList = []
            TempList.append(torrent.name + '\nProgress: ' + str(round(torrent.progress * 100, 2)) + "%" + '\n' + convertTime(torrent.eta))
            MovieList.append(TempList)
        if torrent.category == 'tv-sonarr':
            count = count+1
            TempList = []
            TempList.append(torrent.name + '\nProgress: ' + str(round(torrent.progress * 100, 2)) + "%" + '\n' + convertTime(torrent.eta))
            TVList.append(TempList)
        if torrent.category != 'tv-sonarr' and torrent.category != 'radarr':
            count = count+1
            TempList = []
            TempList.append(torrent.name + '\nProgress: ' + str(round(torrent.progress * 100, 2)) + "%" + '\n' + convertTime(torrent.eta))
            OtherList.append(TempList)

    embed = discord.Embed(
        title="**Torrents**",
        description="Currently Downloading Torrents",
        color=ctx.author.colour
    )
    if count == 0:
        await ctx.send("No Torrents Currently Downloading!",  ephemeral=True)
    else:
        for item in MovieList:
            embed.add_field(name="Movie", value=item[0])
        for item in TVList:
            embed.add_field(name="TV Show", value=item[0])
        for item in OtherList:
            embed.add_field(name="Other" ,value=item[0])
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command()
async def all(ctx: commands.Context):
    MovieList = []
    TVList = []
    OtherList = []
    count=0
    for torrent in qbt_client.torrents.info.all():
        if torrent.category == 'radarr':
            count = count+1
            TempList = []
            TempList.append(torrent.name + '\nProgress: ' + str(round(torrent.progress * 100, 2)) + "%" + '\n' + convertTime(torrent.eta))
            MovieList.append(TempList)
        if torrent.category == 'tv-sonarr':
            count = count+1
            TempList = []
            TempList.append(torrent.name + '\nProgress: ' + str(round(torrent.progress * 100, 2)) + "%" + '\n' + convertTime(torrent.eta))
            TVList.append(TempList)
        if torrent.category != 'tv-sonarr' and torrent.category != 'radarr':
            count = count+1
            TempList = []
            TempList.append(torrent.name + '\nProgress: ' + str(round(torrent.progress * 100, 2)) + "%" + '\n' + convertTime(torrent.eta))
            OtherList.append(TempList)

    embed = discord.Embed(
        title="**Torrents**",
        description="All Torrents",
        color=ctx.author.colour
    )
    if count == 0:
        await ctx.send("No Torrents Currently Downloading!", ephemeral=True)
    else:
        for item in MovieList:
            embed.add_field(name="Movie", value=item[0])
        for item in TVList:
            embed.add_field(name="TV Show", value=item[0])
        for item in OtherList:
            embed.add_field(name="Other" ,value=item[0])
        await ctx.send(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f'{bot.user} is now running! \nMade By @SavnoorSamra')
    await bot.tree.sync()

validate_config()

# qBIT setup
conn_info = dict(host=QBT_HOST)
if QBT_PORT:
    conn_info['port'] = QBT_PORT
if QBT_API_KEY:
    conn_info['api_key'] = QBT_API_KEY
else:
    conn_info['username'] = QBT_USERNAME
    conn_info['password'] = QBT_PASSWORD

qbt_client = qbittorrentapi.Client(**conn_info)

try:
    qbt_client.auth_log_in()
except qbittorrentapi.LoginFailed as e:
    raise SystemExit(f'qBittorrent login failed: {e}') from e

print(f"qBittorrent: {qbt_client.app.version}")
print(f"qBittorrent Web API: {qbt_client.app.web_api_version}")
for k, v in qbt_client.app.build_info.items():
    print(f"{k}: {v}")

def main():
    bot.run(TOKEN)

if __name__ == '__main__':
    main()
