# Telegram YouTube Playlist Bot

A simple Telegram bot that downloads a YouTube playlist in one of two modes:

- `Music only`: extracts audio and converts each item to MP3
- `Video 360p`: downloads each item as video with a 360p cap when available

## What it does

1. You start the bot with `/start`
2. You choose `Music only` or `Video 360p`
3. You paste a YouTube playlist link
4. The bot downloads the playlist and sends the files back in Telegram

## Requirements

- Python 3.12+
- `ffmpeg` installed and available on your `PATH`

`ffmpeg` is required for audio extraction and is strongly recommended for video merging too.

## Setup

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather) and copy the token
2. Create and activate a virtual environment
3. Install the dependencies
4. Copy `.env.example` to `.env`
5. Put your bot token into `.env`

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Then edit `.env` and set:

```env
TELEGRAM_BOT_TOKEN=your_real_bot_token
DOWNLOADS_DIR=downloads
TELEGRAM_MAX_UPLOAD_MB=49
```

## Run

```powershell
python bot.py
```

## Deploy Options

### Option 1: Run on this Windows PC at logon

This keeps the bot running from your machine whenever you sign in.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\deploy-local.ps1
```

The scheduled task uses `run-bot.ps1` and writes logs to `logs\bot.log`.

### Option 2: Deploy in Docker to a cloud host

The project includes a `Dockerfile` that installs Python dependencies and `ffmpeg`.

Typical flow:

1. Push the project to GitHub
2. Create a new service on a host like Railway, Render, or any Docker-friendly VPS
3. Set the `TELEGRAM_BOT_TOKEN` environment variable in the host dashboard
4. Deploy the container

The bot uses polling, so it does not need a public webhook URL.

### Railway

The repo now includes `railway.toml` plus the root `Dockerfile`, which matches Railway's current config-as-code and Docker deployment flow.

1. Push this project to GitHub
2. In Railway, create a new service from that repo
3. Add `TELEGRAM_BOT_TOKEN` in the service Variables tab
4. Deploy

Railway will use the repo's `Dockerfile` automatically when it is present.

### Render

The repo now includes `render.yaml` for a Docker-based background worker, which fits this bot better than a web service because it uses long polling and does not expose HTTP routes.

1. Push this project to GitHub
2. In Render, create a new Blueprint or background worker from the repo
3. Provide `TELEGRAM_BOT_TOKEN` when prompted
4. Deploy the worker

Render background workers are not available on the free plan, so expect to use at least a paid starter-tier worker.

## Commands

- `/start` shows the mode buttons
- `/help` explains the bot flow
- `/cancel` clears the selected mode

## Notes

- The bot expects a playlist link that includes `list=`
- Telegram upload limits still apply, so very large files may be skipped
- Private, region-locked, or unavailable videos may fail or be skipped by `yt-dlp`
- Large playlists can take a while to process

## Project files

- `bot.py`: Telegram bot handlers
- `downloader.py`: playlist download logic using `yt-dlp`
- `config.py`: environment-based configuration loader
