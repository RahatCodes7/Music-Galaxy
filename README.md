# Music Galaxy

![Music Galaxy](https://files.catbox.moe/n83s9g.jpg)

A Telegram music bot customized and maintained under the **Music Galaxy** branding by **@RahatCodes7**.

> Original base by **NoxxOP / ShrutixMusic** — see `LICENSE` for attribution.

## ✨ Features

- 🎵 Telegram music playback in voice chats
- 🔍 YouTube / Spotify / SoundCloud search & streaming
- ⏯ Queue management — play, skip, pause, resume, stop, shuffle, loop, seek, speed
- 📜 MongoDB-backed configuration & chat management
- 🔧 Environment-variable deployment (VPS / Docker / Render / Heroku)
- 👮 Admin controls, auth users, broadcast, maintenance mode & more

## 🚀 Commands

### Playback
- `/play` / `/vplay` — Play audio / video
- `/pause` / `/resume` — Pause / resume
- `/skip` — Skip track (supports `/skip 2` for queue jump)
- `/stop` / `/end` — Stop & clear queue
- `/queue` — Show queued tracks
- `/song` — Download track as mp3/mp4
- `/seek` / `/seekback` — Seek in stream
- `/speed` — Playback speed control
- `/loop` — Loop current stream
- `/shuffle` — Shuffle queue
- `/player` — Interactive player panel

> Full command list available via `/help` inside Telegram.

## 🛠️ Local / VPS Deployment

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

### Systemd (persistent VPS)

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

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now musicgalaxy
sudo systemctl status musicgalaxy
```

## 🐳 Docker

```bash
docker build -t music-galaxy .
docker run --env-file .env music-galaxy
```

`Dockerfile` already handles `ffmpeg` install and uses `python3 -m MusicGalaxy`.

## ☁️ Render & Heroku

- **Render:** uses `render.yaml` worker — create project from GitHub repo, add env vars, deploy.
- **Heroku:** uses `heroku.yml` + `Procfile` (`worker: bash start`) — set env vars in dashboard and deploy.

## ⚙️ Configuration

Copy `.env.example` → `.env` and fill:

```
API_ID / API_HASH / BOT_TOKEN / MONGO_DB_URI / OWNER_ID / LOGGER_ID / STRING_SESSION ...
UPSTREAM_REPO=https://github.com/RahatCodes7/Music-Galaxy.git
SUPPORT_CHAT=https://t.me/your_group
SUPPORT_CHANNEL=https://t.me/your_channel
START_IMG_URL=...
YUKI_API_URL=https://music.yukiapi.site
YUKI_API_KEY=...
```

**Never commit `.env`, bot tokens, API keys or Pyrogram session strings.**

## 📂 Project Structure

```
.
├── MusicGalaxy/          # Main bot package (renamed from ShrutixMusic)
├── strings/              # i18n (en.yml, hi.yml, ar.yml, pa.yml)
├── requirements.txt
├── Procfile              # worker: bash start
├── heroku.yml
├── runtime.txt
├── .env.example
├── .gitignore
└── README.md
```

## 📄 License & Attribution

This project contains code derived from upstream **ShrutixMusic** (`NoxxOP/ShrutixMusic`). Upstream license & attribution retained in `LICENSE`.

Music Galaxy branding, config & customization maintained by **@RahatCodes7**.

See `LICENSE` before redistributing.

## 💬 Support

- Support Chat: `https://t.me/your_group`
- Updates Channel: `https://t.me/your_channel`
- Creator: **@RahatCodes7**

> Replace placeholder links in `.env` / `config.py` with your actual Telegram groups.

