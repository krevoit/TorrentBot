# Torrent Bot

A small Discord bot for checking qBittorrent download status from slash commands.

Repository: [github.com/krevoit/TorrentBot](https://github.com/krevoit/TorrentBot)

## Features

- `/downloading` shows active torrents grouped by Radarr, Sonarr, and other categories.
- `/all` shows every torrent currently known to qBittorrent.
- Optional live progress updates for `/downloading`.
- Approved users can subscribe to category/tag completion notifications.
- Commands are DM-only and restricted to approved Discord users.
- Supports qBittorrent username/password auth and qBittorrent Web API key auth.
- Runs locally or in Docker.

## Requirements

- A Discord bot token.
- qBittorrent Web UI enabled.
- Python 3.14 or Docker.

## Discord Setup

1. Go to [discord.dev](https://discord.dev) and create an application.
2. Open the **Bot** page and copy the bot token.
3. Enable Message Content Intent if you want to use typed DM commands like `/all`.
4. Open **OAuth2**, generate a bot invite URL, and add the bot to your server.

![Discord bot permissions](img/permissions.png)

## Configuration

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_discord_bot_token
QBT_HOST=127.0.0.1
QBT_PORT=8080
QBT_USERNAME=admin
QBT_PASSWORD=your_password
APPROVED_USER_IDS=123456789012345678,234567890123456789
```

For qBittorrent versions that support Web API keys, use `QBT_API_KEY` instead of username/password:

```env
DISCORD_TOKEN=your_discord_bot_token
QBT_HOST=127.0.0.1
QBT_PORT=8080
QBT_API_KEY=your_qbittorrent_api_key
APPROVED_USER_IDS=123456789012345678,234567890123456789
```

`QBT_PORT` is optional if the port is already included in `QBT_HOST`.
`APPROVED_USER_IDS` is a comma-separated list of Discord user IDs allowed to use the bot.

Optional tuning:

```env
LIVE_UPDATE_INTERVAL_SECONDS=30
LIVE_UPDATE_COUNT=20
SUBSCRIPTION_POLL_SECONDS=60
SUBSCRIPTIONS_FILE=subscriptions.json
```

## Run With Docker

Using Docker Hub:

```sh
docker run --env-file .env krevoit/torrentbot:latest
```

Using GitHub Container Registry:

```sh
docker run --env-file .env ghcr.io/krevoit/torrentbot:latest
```

Using Docker Compose:

```yaml
services:
  torrentbot:
    image: krevoit/torrentbot:latest
    container_name: torrentbot
    env_file:
      - .env
    environment:
      SUBSCRIPTIONS_FILE: /data/subscriptions.json
    volumes:
      - ./data:/data
    restart: unless-stopped
```

Start it with:

```sh
docker compose up -d
```

To build locally from source:

```sh
git clone https://github.com/krevoit/TorrentBot.git
cd TorrentBot
docker build -t torrentbot .
docker run --env-file .env torrentbot
```

The Docker image uses `python:3.14-slim`.

## Publishing

Docker images are published by GitHub Actions on pushes to `main`:

- Docker Hub: `krevoit/torrentbot:latest`
- GitHub Container Registry: `ghcr.io/krevoit/torrentbot:latest`

Docker Hub publishing requires these repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## Run Locally

```sh
python3.14 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Commands

Commands are run in DMs with the bot. Server/channel commands are rejected.

- `/downloading` - shows currently downloading torrents.
- `/downloading category:radarr live:true` - edits the same message with fresh progress.
- `/downloading category:tv-sonarr tag:priority` - filters active downloads by category and tag.
- `/all` - shows all torrents in qBittorrent.
- `/subscribe category:radarr` - DMs you current matching progress and pings when matching downloads finish.
- `/subscribe category:games user:@brother` - sends progress and completion DMs to another user.
- `/subscribe category:tv-sonarr tag:priority` - subscribes to a narrower category/tag filter.
- `/unsubscribe category:radarr user:@brother` - removes a matching subscription.
- `/subscriptions` - shows your active subscriptions.
- `/subscriptions user:@brother` - shows another user's active subscriptions.

All commands are only available to users listed in `APPROVED_USER_IDS`.

## Acknowledgments

- [qbittorrent-api](https://github.com/rmartin16/qbittorrent-api)
- [QBitHelper](https://github.com/Opaque02/QBitHelper/tree/main)
