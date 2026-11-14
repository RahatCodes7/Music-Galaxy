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
MONGO_DB_NAME / MONGO_TIMEOUT_MS / MONGO_DIRECT_CONNECTION (optional)
UPSTREAM_REPO=https://github.com/RahatCodes7/Music-Galaxy.git
SUPPORT_CHAT=https://t.me/your_group
SUPPORT_CHANNEL=https://t.me/your_channel
START_IMG_URL=...
DOWNLOAD_API_URL=https://dltapi.cc.cd
DOWNLOAD_API_KEY=dl_live_IMbe7IFdA-9pgZd1IgEKnFRBvEOwEC00Om1RSzUJStw
# Back-compat aliases: YUKI_API_URL / YUKI_API_KEY, DLT_API_URL / DLT_API_KEY
```

**Never commit `.env`, bot tokens, API keys or Pyrogram session strings.**

## 🗄️ MongoDB troubleshooting

The bot talks to **one** MongoDB. A local install works exactly like Atlas, the
only difference is the URI:

```ini
# local mongod on this machine
MONGO_DB_URI=mongodb://127.0.0.1:27017/musicgalaxy

# mongod in docker compose (service name is the host)
MONGO_DB_URI=mongodb://mongo:27017/musicgalaxy

# Atlas
MONGO_DB_URI=mongodb+srv://user:password@cluster.mongodb.net/musicgalaxy
```

Check the connection **without starting the bot**:

```bash
python3 dbcheck.py
# or test a specific URI
python3 dbcheck.py "mongodb://127.0.0.1:27017/musicgalaxy"
```

It runs three checks and prints the failing one: configuration → TCP
reachability → real `ping`. Exit code `0` means the bot will connect.

Common causes of `Failed to connect to your Mongo Database`:

| Symptom | Cause / fix |
| --- | --- |
| `MONGO_DB_URI is empty` | `.env` not found or the key is missing. Start the bot from the repo root, or keep `.env` next to `config.py`. |
| `MONGO_DB_URI still contains the .env.example placeholder` | You copied `.env.example` and never replaced `your_mongodb_uri`. |
| `Connection refused` (`127.0.0.1:27017`) | `mongod` is not running: `sudo systemctl start mongod`, or `docker start mongo`. |
| `Authentication failed` | Wrong user/password, or the user lives in `admin`: append `?authSource=admin`. |
| `Username and password must be escaped` | Password has `@ : / #` — encode it with `python3 -c "import urllib.parse,sys;print(urllib.parse.quote_plus(sys.argv[1]))" 'p@ss'`. |
| Connects, but your data is "missing" | The bot writes into the database named in the URI path, else `MusicGalaxy`. Open that db in Compass, or force it with `MONGO_DB_NAME=...`. |
| `ReplicaSetNoPrimary` on a local single node | Add `?directConnection=true` (or `MONGO_DIRECT_CONNECTION=true`). |

Notes:

- `localhost` is rewritten to `127.0.0.1` automatically, which avoids the
  IPv6 (`::1`) vs IPv4 listen-address mismatch of a local `mongod`.
- `MONGO_TIMEOUT_MS` (default `8000`) controls how long a connection attempt is
  retried before the bot gives up; startup retries 3 times, so a database that
  boots a few seconds after the bot still works.
- Credentials are never written to `log.txt` — logged URIs are masked.
- MongoDB requires `dnspython` for `mongodb+srv://` URIs; it is in
  `requirements.txt`, so install the requirements inside the same venv the bot
  runs from.

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

