# Torrent Bot

A small Discord bot for checking qBittorrent download status from slash commands.

Repository: [github.com/krevoit/TorrentBot](https://github.com/krevoit/TorrentBot)

## Features

- `/downloading` shows active torrents grouped by Radarr, Sonarr, and other categories.
- `/all` shows every torrent currently known to qBittorrent.
- Supports qBittorrent username/password auth and qBittorrent Web API key auth.
- Runs locally or in Docker.

## Requirements

- A Discord bot token.
- qBittorrent Web UI enabled.
- Python 3.14 or Docker.

## Discord Setup

1. Go to [discord.dev](https://discord.dev) and create an application.
2. Open the **Bot** page and copy the bot token.
3. Enable the intents your server requires. The bot currently uses Discord slash commands.
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
```

For qBittorrent versions that support Web API keys, use `QBT_API_KEY` instead of username/password:

```env
DISCORD_TOKEN=your_discord_bot_token
QBT_HOST=127.0.0.1
QBT_PORT=8080
QBT_API_KEY=your_qbittorrent_api_key
```

`QBT_PORT` is optional if the port is already included in `QBT_HOST`.

## Run With Docker

Using Docker Hub:

```sh
docker run --env-file .env krevoit/torrentbot:latest
```

Using GitHub Container Registry:

```sh
docker run --env-file .env ghcr.io/krevoit/torrentbot:latest
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

- `/downloading` - shows currently downloading torrents.
- `/all` - shows all torrents in qBittorrent.

## Acknowledgments

- [qbittorrent-api](https://github.com/rmartin16/qbittorrent-api)
- [QBitHelper](https://github.com/Opaque02/QBitHelper/tree/main)
