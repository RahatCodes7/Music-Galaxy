# Music Galaxy Music Bot

A Telegram music bot customized and maintained under the **Music Galaxy** branding.

## Branding

- Updates: https://t.me/your_channel
- Support: https://t.me/your_group
- Creator: @RahatCodes7

## Features

- Telegram music playback
- YouTube/music search and playback
- Voice-chat controls
- Queue management
- Pause / resume / skip / replay controls
- MongoDB-backed configuration
- Environment-variable based deployment
- VPS/systemd, Render and Heroku deployment files

## Commands

### Playback
- `/play` — Play a song
- `/vplay` — Play with video
- `/pause` — Pause playback
- `/resume` — Resume playback
- `/skip` — Skip the current track
- `/stop` — Stop playback
- `/queue` — Show the current queue
- `/song` — Download a requested track

> The exact command set can vary with the enabled modules and configuration in this source tree.

## Local / VPS deployment

```bash
git clone https://github.com/RahatCodes7/Music-Galaxy.git
cd Music-Galaxy

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

cp .env.example .env
nano .env

python3 -m MusicGalaxy
```

For persistent VPS deployment, use systemd:

```ini
[Unit]
Description=Music Galaxy Music Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Music-Galaxy
EnvironmentFile=/home/ubuntu/Music-Galaxy/.env
Environment="PATH=/home/ubuntu/Music-Galaxy/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/ubuntu/Music-Galaxy/venv/bin/python3 -m MusicGalaxy
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now musicgalaxy
sudo systemctl status musicgalaxy
```

## Render

This repository includes `render.yaml`.

1. Create a new Render project from the GitHub repository.
2. Use the worker service defined in `render.yaml`.
3. Add the required Telegram, database, owner and assistant-session variables.
4. Deploy.

## Heroku

The repository includes `heroku.yml` and `Procfile`.

Set the required environment variables in the Heroku dashboard and deploy the repository using the worker process.

## Configuration

Copy `.env.example` to `.env` and fill in the required values.

**Never commit `.env`, bot tokens, API keys, database credentials or Pyrogram session strings.**

## Project structure

```text
.
├── MusicGalaxy/
├── strings/
├── requirements.txt
├── Procfile
├── render.yaml
├── heroku.yml
├── runtime.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## License and attribution

This project contains code derived from the upstream MusicGalaxy project. The upstream license and attribution requirements are retained in `LICENSE`.

Music Galaxy-specific branding, configuration and customization are maintained by **@RahatCodes7**.

See `LICENSE` before redistributing or publishing modified copies.
