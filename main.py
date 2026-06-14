import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import discord
import qbittorrentapi
from discord import Intents
from discord.ext import commands, tasks
from dotenv import load_dotenv

from functions import convertTime


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
QBT_HOST = os.getenv('QBT_HOST')
QBT_PORT = os.getenv('QBT_PORT')
QBT_USERNAME = os.getenv('QBT_USERNAME')
QBT_PASSWORD = os.getenv('QBT_PASSWORD')
QBT_API_KEY = os.getenv('QBT_API_KEY')
APPROVED_USER_IDS = {
    int(user_id.strip())
    for user_id in os.getenv('APPROVED_USER_IDS', '').split(',')
    if user_id.strip().isdigit()
}
SUBSCRIPTIONS_FILE = Path(os.getenv('SUBSCRIPTIONS_FILE', 'subscriptions.json'))
LIVE_UPDATE_INTERVAL_SECONDS = int(os.getenv('LIVE_UPDATE_INTERVAL_SECONDS', '30'))
LIVE_UPDATE_COUNT = int(os.getenv('LIVE_UPDATE_COUNT', '20'))
SUBSCRIPTION_POLL_SECONDS = int(os.getenv('SUBSCRIPTION_POLL_SECONDS', '60'))

CATEGORY_LABELS = {
    'radarr': 'Movies',
    'tv-sonarr': 'TV Shows',
}
EMBED_COLORS = {
    'downloading': discord.Color.blurple(),
    'all': discord.Color.teal(),
    'complete': discord.Color.green(),
    'empty': discord.Color.dark_gray(),
}


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


def parse_torrent_tags(torrent):
    tags = getattr(torrent, 'tags', '') or ''
    if isinstance(tags, (list, tuple, set)):
        return {str(tag).strip().lower() for tag in tags if str(tag).strip()}
    return {tag.strip().lower() for tag in tags.split(',') if tag.strip()}


def torrent_matches(torrent, category=None, tag=None):
    if category and (torrent.category or '').lower() != category.lower():
        return False
    if tag and tag.lower() not in parse_torrent_tags(torrent):
        return False
    return True


def category_name(category):
    if not category:
        return 'Other'
    return CATEGORY_LABELS.get(category, category)


def progress_bar(progress, width=14):
    completed = min(width, max(0, round(progress * width)))
    return '█' * completed + '░' * (width - completed)


def torrent_line(torrent):
    percent = round(torrent.progress * 100, 1)
    state = getattr(torrent, 'state', 'unknown')
    eta = convertTime(torrent.eta)
    return (
        f"**{torrent.name}**\n"
        f"`{progress_bar(torrent.progress)}` {percent}%\n"
        f"{eta} • `{state}`"
    )


def matching_torrents(mode, category=None, tag=None):
    torrent_source = qbt_client.torrents.info.active() if mode == 'downloading' else qbt_client.torrents.info.all()
    return [torrent for torrent in torrent_source if torrent_matches(torrent, category, tag)]


def build_torrent_embed(mode, category=None, tag=None):
    torrents = matching_torrents(mode, category, tag)
    title = 'Active Downloads' if mode == 'downloading' else 'All Torrents'
    filters = []
    if category:
        filters.append(f"category `{category}`")
    if tag:
        filters.append(f"tag `{tag}`")
    description = f"Filtered by {' and '.join(filters)}" if filters else 'qBittorrent status'

    embed = discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLORS[mode] if torrents else EMBED_COLORS['empty'],
    )
    embed.set_footer(text=f"{len(torrents)} torrent{'s' if len(torrents) != 1 else ''} matched")

    if not torrents:
        embed.add_field(name='Nothing to show', value='No matching torrents right now.', inline=False)
        return embed

    grouped = {}
    for torrent in torrents[:25]:
        grouped.setdefault(category_name(torrent.category), []).append(torrent)

    for label, group in grouped.items():
        value = '\n\n'.join(torrent_line(torrent) for torrent in group)
        embed.add_field(name=label, value=value[:1024], inline=False)

    if len(torrents) > 25:
        embed.add_field(
            name='More torrents',
            value=f"{len(torrents) - 25} additional torrents were hidden to keep the embed readable.",
            inline=False,
        )

    return embed


def load_subscriptions():
    if not SUBSCRIPTIONS_FILE.exists():
        return {}
    with SUBSCRIPTIONS_FILE.open('r', encoding='utf-8') as subscriptions_file:
        return json.load(subscriptions_file)


def save_subscriptions():
    with SUBSCRIPTIONS_FILE.open('w', encoding='utf-8') as subscriptions_file:
        json.dump(subscriptions, subscriptions_file, indent=2)


def is_approved(user_id):
    return user_id in APPROVED_USER_IDS


def subscription_key(category=None, tag=None):
    return f"{category or '*'}|{tag or '*'}"


def get_torrent_hash(torrent):
    return getattr(torrent, 'hash', torrent.name)


def is_complete(torrent):
    return torrent.progress >= 1


def subscription_matches(subscription, torrent):
    return torrent_matches(torrent, subscription.get('category'), subscription.get('tag'))


def seed_pending_hashes(subscription):
    pending = set(subscription.get('pending_hashes', []))
    for torrent in qbt_client.torrents.info.all():
        if subscription_matches(subscription, torrent) and not is_complete(torrent):
            pending.add(get_torrent_hash(torrent))
    subscription['pending_hashes'] = sorted(pending)


validate_config()

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
subscriptions = load_subscriptions()


@bot.check
async def approved_dm_context(ctx):
    if ctx.guild is not None:
        await ctx.send('DM me to use Torrent Bot commands.', ephemeral=True)
        return False
    if not is_approved(ctx.author.id):
        await ctx.send('You are not approved to use Torrent Bot commands.', ephemeral=True)
        return False
    return True


async def approved_dm_interaction(interaction):
    if interaction.guild is not None:
        await interaction.response.send_message('DM me to use Torrent Bot commands.', ephemeral=True)
        return False
    if not is_approved(interaction.user.id):
        await interaction.response.send_message('You are not approved to use Torrent Bot commands.', ephemeral=True)
        return False
    return True


bot.tree.interaction_check = approved_dm_interaction

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


async def send_torrent_status(ctx, mode, category=None, tag=None, live=False):
    embed = build_torrent_embed(mode, category, tag)
    message = await ctx.send(embed=embed, ephemeral=not live)

    if not live:
        return

    for _ in range(LIVE_UPDATE_COUNT):
        await asyncio.sleep(LIVE_UPDATE_INTERVAL_SECONDS)
        await message.edit(embed=build_torrent_embed(mode, category, tag))


@bot.hybrid_command()
async def downloading(
    ctx: commands.Context,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    live: bool = False,
):
    await send_torrent_status(ctx, 'downloading', category, tag, live)


@bot.hybrid_command(name='all')
async def all_torrents(
    ctx: commands.Context,
    category: Optional[str] = None,
    tag: Optional[str] = None,
):
    await send_torrent_status(ctx, 'all', category, tag)


@bot.hybrid_command()
async def subscribe(
    ctx: commands.Context,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    user: Optional[discord.User] = None,
):
    if not is_approved(ctx.author.id):
        await ctx.send('You are not approved to subscribe to download notifications.', ephemeral=True)
        return
    if not category and not tag:
        await ctx.send('Choose a category, a tag, or both for the subscription.', ephemeral=True)
        return

    target_user = user or ctx.author
    user_id = str(target_user.id)
    subscriptions.setdefault(user_id, {})
    key = subscription_key(category, tag)
    subscription = {
        'category': category,
        'tag': tag,
        'created_by': str(ctx.author.id),
        'pending_hashes': [],
    }
    seed_pending_hashes(subscription)
    subscriptions[user_id][key] = subscription
    save_subscriptions()

    await ctx.send(
        f"Subscribed {target_user.mention} to downloads matching category `{category or '*'}` and tag `{tag or '*'}`.",
        ephemeral=True,
    )

    try:
        await target_user.send(embed=build_torrent_embed('downloading', category, tag))
    except discord.Forbidden:
        await ctx.send(
            f"I could not DM {target_user.mention}. They may need to enable DMs from this server.",
            ephemeral=True,
        )


@bot.hybrid_command()
async def unsubscribe(
    ctx: commands.Context,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    user: Optional[discord.User] = None,
):
    if not is_approved(ctx.author.id):
        await ctx.send('You are not approved to manage download notifications.', ephemeral=True)
        return

    target_user = user or ctx.author
    user_id = str(target_user.id)
    key = subscription_key(category, tag)
    if subscriptions.get(user_id, {}).pop(key, None) is None:
        await ctx.send('No matching subscription found.', ephemeral=True)
        return
    if not subscriptions[user_id]:
        subscriptions.pop(user_id)
    save_subscriptions()
    await ctx.send(
        f"Unsubscribed {target_user.mention} from category `{category or '*'}` and tag `{tag or '*'}`.",
        ephemeral=True,
    )


@bot.hybrid_command(name='subscriptions')
async def subscriptions_list(ctx: commands.Context, user: Optional[discord.User] = None):
    if not is_approved(ctx.author.id):
        await ctx.send('You are not approved to view download subscriptions.', ephemeral=True)
        return

    target_user = user or ctx.author
    user_subscriptions = subscriptions.get(str(target_user.id), {})
    if not user_subscriptions:
        await ctx.send(f'{target_user.mention} does not have any active subscriptions.', ephemeral=True)
        return

    embed = discord.Embed(title=f'Download Subscriptions for {target_user.display_name}', color=discord.Color.gold())
    for subscription in user_subscriptions.values():
        embed.add_field(
            name=f"Category: {subscription.get('category') or '*'}",
            value=f"Tag: `{subscription.get('tag') or '*'}`",
            inline=False,
        )
    await ctx.send(embed=embed, ephemeral=True)


@tasks.loop(seconds=SUBSCRIPTION_POLL_SECONDS)
async def check_subscriptions():
    if not subscriptions:
        return

    changed = False
    try:
        torrents = qbt_client.torrents.info.all()
    except qbittorrentapi.APIError as error:
        print(f'Could not check qBittorrent subscriptions: {error}')
        return

    for user_id, user_subscriptions in list(subscriptions.items()):
        user = bot.get_user(int(user_id)) or await bot.fetch_user(int(user_id))
        for subscription in user_subscriptions.values():
            pending = set(subscription.get('pending_hashes', []))
            for torrent in torrents:
                if not subscription_matches(subscription, torrent):
                    continue

                torrent_hash = get_torrent_hash(torrent)
                if not is_complete(torrent):
                    if torrent_hash not in pending:
                        pending.add(torrent_hash)
                        changed = True
                    continue

                if torrent_hash not in pending:
                    continue

                pending.remove(torrent_hash)
                changed = True
                embed = discord.Embed(
                    title='Download Complete',
                    description=f"{user.mention} **{torrent.name}** finished downloading.",
                    color=EMBED_COLORS['complete'],
                )
                embed.add_field(name='Category', value=torrent.category or 'None', inline=True)
                embed.add_field(name='Tags', value=getattr(torrent, 'tags', '') or 'None', inline=True)
                try:
                    await user.send(embed=embed)
                except discord.Forbidden:
                    print(f'Could not DM completion notice to user {user_id}')
            subscription['pending_hashes'] = sorted(pending)

    if changed:
        save_subscriptions()


@check_subscriptions.before_loop
async def before_check_subscriptions():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f'{bot.user} is now running! \nMade By @SavnoorSamra')
    await bot.tree.sync()
    if not check_subscriptions.is_running():
        check_subscriptions.change_interval(seconds=SUBSCRIPTION_POLL_SECONDS)
        check_subscriptions.start()


def main():
    bot.run(TOKEN)


if __name__ == '__main__':
    main()
