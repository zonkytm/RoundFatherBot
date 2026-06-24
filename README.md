# RoundFather Bot

Telegram bot that converts videos to circular Video Notes with a web dashboard, premium subscriptions, and mailing system.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![aiogram](https://img.shields.io/badge/aiogram-3.x-green)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Video to Circle** -- converts any video to 360x360 Video Note (H.264+AAC, max 60s)
- **Premium Subscriptions** -- 1/3/6 month packages with Telegram Stars payment
- **Daily Limits** -- 10 videos/day for free users, unlimited for premium
- **Web Dashboard** -- admin panel with stats, mailings, revenue tracking
- **Mailing System** -- one-time, scheduled, and recurring broadcasts with cron
- **Revenue Tracking** -- monthly stats, package breakdown, conversion metrics
- **Prometheus Metrics** -- `/metrics` endpoint for monitoring
- **Health Checks** -- `/health` and `/ready` endpoints
- **Alembic Migrations** -- versioned database schema management

## Architecture

```
bot-qwen/
  bot/               # aiogram bot
    handlers/        # command & message handlers
    middlewares/      # rate limit, metrics, db session
    services/        # video processing, notifications, stats
    models/          # SQLAlchemy 2.0 async models
  web/               # FastAPI dashboard
    routes/          # API endpoints (stats, mailings, revenue, auth)
    templates/       # Jinja2 HTML templates
  alembic/           # database migrations
  docker/            # Dockerfiles
  tests/             # unit tests
```

## Quick Start

### Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/yourname/roundfather-bot.git
cd roundfather-bot

# 2. Configure environment
cp .env.example .env
# Edit .env with your BOT_TOKEN, ADMIN_IDS, DASHBOARD_TOKEN

# 3. Start all services
docker compose up -d

# 4. Check status
docker compose ps
docker compose logs bot
```

Services: `bot`, `worker`, `web` (port 8000), `redis`, `postgres`

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Start database (Docker)
docker compose up -d redis postgres

# Run bot
python -m bot.main

# Run worker (separate terminal)
arq bot.services.tasks.WorkerSettings

# Run dashboard (separate terminal)
uvicorn web.app:app --reload --port 8000

# Run tests
pytest tests/ -v
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with status & premium buttons |
| `/status` | Show daily limit and premium status |
| `/premium` | View premium packages and purchase |
| `/stats` | (Admin) Bot statistics |
| `/blocked` | (Admin) List blocked users |
| `/unblock <id>` | (Admin) Unblock a user |

## Dashboard

Access at `http://localhost:8000` (login with `DASHBOARD_TOKEN`).

- **Dashboard** -- user/video stats, activity chart
- **Mailings** -- create and manage broadcasts
- **Revenue** -- payment stats, package breakdown, conversion

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | -- |
| `BOT_USERNAME` | Bot username | -- |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `DATABASE_URL` | PostgreSQL async URL | `postgresql+asyncpg://postgres:postgres@localhost:5432/bot_qwen` |
| `ADMIN_IDS` | JSON list of admin Telegram IDs | `[]` |
| `WEBAPP_URL` | Dashboard public URL | `http://localhost:8000` |
| `DASHBOARD_TOKEN` | Admin dashboard access token | -- |
| `RATE_LIMIT_PER_MINUTE` | Max videos per user per minute | `5` |

## Tech Stack

- **Bot** -- Python 3.11, aiogram 3.x, SQLAlchemy 2.0 (async), arq + Redis
- **Dashboard** -- FastAPI, Jinja2, Chart.js, Tailwind CSS
- **Database** -- PostgreSQL 16, Alembic
- **Video** -- FFmpeg (async subprocess)
- **Infrastructure** -- Docker Compose, Prometheus

## License

MIT
