nano README.md
markdown# MTF Trading Strategy Bot

Multi-timeframe cryptocurrency trading bot with RSI and breakout strategies.

## Features
- Multi-timeframe analysis (15m, 30m, 1h, 4h)
- RSI mean reversion in ranging markets
- Breakout trading in trending markets
- Telegram notifications
- Risk management with stop-loss/take-profit

## Quick Start
1. Copy `config/config.example.yaml` to `config/config.yaml`
2. Create `config/.env` with your API keys
3. Run: `docker compose up -d`

## Management
- Start: `./scripts/start.sh`
- Stop: `./scripts/stop.sh`
- Update: `./scripts/update.sh`
- Logs: `docker compose logs -f`

## Monitoring
- Portainer: http://your-server:9000
- Telegram notifications enabled


