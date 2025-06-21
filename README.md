# Multi-Timeframe Hybrid Crypto Trading Bot

---

## 🚀 Overview

This project provides a robust and configurable cryptocurrency trading bot designed for multi-timeframe analysis. It leverages a hybrid strategy combining **RSI Mean Reversion** for ranging markets and **Price Breakout** for trending markets. Built with **Python** and **Docker Compose**, the bot offers a clean, containerized environment for reliable operation and easy deployment.

Currently, the bot focuses on **signal generation and notification via Telegram**, operating exclusively in a **sandbox (testnet) environment** to ensure safe testing without risking real capital.

---

## ✨ Features

* **Multi-Timeframe Analysis (MTFA):** Utilizes multiple timeframes (15m, 30m, 1h, 4h) for comprehensive market context, trend alignment, and regime analysis.
* **Hybrid Strategy:**
    * **RSI Mean Reversion:** Identifies potential reversals in ranging market conditions.
    * **Price Breakout:** Captures momentum during trending market phases.
* **Dynamic Market Regime Detection:** Employs ADX to identify trending vs. ranging markets, enabling adaptive strategy execution.
* **Trend Alignment Filter:** Ensures signals align with the broader market trend across multiple timeframes.
* **Volatility Filter:** Incorporates ATR to ensure sufficient market volatility for trade opportunities.
* **Telegram Notifications:** Sends real-time BUY/SELL signals and bot status updates directly to your Telegram chat.
* **Highly Configurable:** All trading parameters, strategy thresholds, symbols, and timeframes are externalized in `config.yaml`.
* **Containerized Deployment:** Uses Docker and Docker Compose for a consistent, isolated, and reproducible environment.
* **Sandbox Mode:** Safely test strategies on exchange testnets without financial risk.
* **Persistent Logging:** Logs are stored on your host machine for easy monitoring and debugging.

---

## 📂 Project Structure

.
├── trading_bot.py      # Core trading logic, strategy implementation, and signal generation.
├── config.yaml         # Centralized configuration for bot parameters, strategy settings, and symbols.
├── requirements.txt    # Lists all Python dependencies.
├── Dockerfile          # Instructions to build the Docker image for the trading bot.
├── docker-compose.yaml # Defines the Docker services (currently just the bot), networks, and volumes.
└── .env                # Stores sensitive environment variables (API keys, Telegram tokens).


---

## 🛠️ Getting Started

Follow these steps to get your bot up and running.

### Prerequisites

* **Docker Desktop:** Make sure Docker is installed and running on your system.
    * [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
* **Docker Compose:** Typically comes bundled with Docker Desktop. Verify installation with `docker compose version`.

### Setup

1.  **Clone the Repository (or create files):**
    If you haven't already, save all the provided files (`trading_bot.py`, `config.yaml`, `requirements.txt`, `Dockerfile`, `docker-compose.yaml`, `.env`) into a dedicated project directory on your local machine.

2.  **Configure `.env` (Crucial for Testnet!):**
    Create a file named `.env` in the root of your project directory (where `docker-compose.yaml` is located). Populate it with your API keys and Telegram details.

    **⚠️ IMPORTANT: For testing, you MUST use API keys from the exchange's TESTNET, not your live trading account.** Most exchanges offer a separate website/portal for testnet accounts where you can generate these keys and get free test funds.

    ```dotenv
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID

    # Exchange API Configuration (USE TESTNET KEYS HERE!)
    EXCHANGE_API_KEY=YOUR_EXCHANGE_TESTNET_API_KEY
    EXCHANGE_SECRET=YOUR_EXCHANGE_TESTNET_SECRET

    # Bot Configuration
    BOT_NAME=MTF-Strategy-Bot
    LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
    SANDBOX_MODE=true       # Set to 'false' ONLY for live trading (after extensive testing!)
    ```
    * **`TELEGRAM_BOT_TOKEN`**: Get this from BotFather on Telegram.
    * **`TELEGRAM_CHAT_ID`**: Forward a message from your bot to the [@userinfobot](https://t.me/userinfobot) to get your chat ID. Ensure your bot is added to the chat where you want to receive notifications.
    * **`EXCHANGE_API_KEY` / `EXCHANGE_SECRET`**: Obtain these from your chosen exchange's **testnet** platform (e.g., `testnet.binancefuture.com` for Binance Futures).
    * **`SANDBOX_MODE=true`**: This is paramount for safe testing. Your bot is currently configured to connect to the testnet when this is `true`.

3.  **Customize `config.yaml`:**
    Open `config.yaml` and adjust the `trading` parameters, `strategy` thresholds, `symbols` to monitor, `timeframes`, and `risk_management` settings to suit your preferences.

    ```yaml
    # Example snippet from config.yaml
    trading:
      leverage: 5
      base_capital: 100.0
      check_interval: 300 # seconds between checks
      sandbox_mode: true  # This will be overridden by SANDBOX_MODE in .env if present

    strategy:
      rsi:
        period: 14
        buy_threshold: 40.0
        # ...
    # ...and so on for other sections
    ```

### Building and Running the Bot

Navigate to your project directory in the terminal and run the following commands:

1.  **Build the Docker image:**
    This command compiles the `TA-Lib` C library and installs all Python dependencies within the Docker image. This may take a few minutes on the first run.

    ```bash
    docker compose build
    ```

2.  **Start the bot services:**
    This will start your trading bot container in the background (`-d` for detached mode).

    ```bash
    docker compose up -d
    ```

3.  **Monitor the bot's logs:**
    To see the bot's output, including connection status, analysis, and potential errors:

    ```bash
    docker compose logs -f trading-bot
    ```

    You should see a "Bot Started" message in your Telegram chat if notifications are enabled and configured correctly.

---

## 🧪 Testing (Sandbox Mode)

Your bot is currently configured for **sandbox (testnet) trading only**. This is critical for strategy validation without financial risk.

### Key Aspects of Testing:

* **Testnet API Keys & Funds:**
    * Ensure your `.env` contains **API keys specifically for the exchange's testnet**.
    * Fund your testnet account with "play money" using the exchange's testnet faucet.
* **Signal Observation:**
    * Monitor the Telegram messages sent by your bot.
    * When a signal is sent, manually compare it to the current market conditions on the **exchange's testnet chart** for the given symbol and timeframe.
    * Does the RSI value match? Is the price truly breaking out? Does the trend align? This manual verification builds confidence.
* **Bot Behavior:**
    * Check the Docker logs (`docker compose logs -f trading-bot`) for any errors, warnings, or unexpected behavior.
    * Verify that the `check_interval` and `cooldown_period` are functioning as expected.
* **No Live Trades:** Reconfirm that no real money is involved. The bot will *not* place actual orders on the live market in its current configuration.

---

## 📈 Strategy Overview

The bot employs a **Multi-Timeframe Hybrid Strategy**:

* **Market Regime Detection (1h, 4h ADX):** First, it identifies if the market for a given symbol is currently **trending** or **ranging** based on higher timeframe ADX values.
* **Overall Trend Alignment (All Timeframes EMA):** It then checks for a consistent trend across all configured timeframes (15m, 30m, 1h, 4h) by comparing the current price to the Exponential Moving Averages (EMAs) on each timeframe. This acts as a primary filter.
* **Volatility Filter (1h ATR):** Ensures there's enough volatility in the market (based on Average True Range) for a trade to be worthwhile.
* **Signal Generation (1h):**
    * **RSI Mean Reversion:** If the market is **ranging**, and the RSI on the **1-hour timeframe** crosses specific oversold/overbought thresholds (e.g., <40 for buy, >60 for sell), a signal is generated. These signals are filtered by the overall trend bias (e.g., only buy in a bullish ranging market).
    * **Price Breakout:** If the market is **trending**, and the price on the **1-hour timeframe** breaks out above a recent highest high or below a recent lowest low, a signal is generated. These are also filtered by the overall trend bias.

---

## ⚠️ Disclaimer

This trading bot is provided for educational and informational purposes only. It is intended for use in simulated (sandbox/testnet) environments. **Using any automated trading system with real money carries significant financial risk.** Do your own thorough research, backtesting, and paper trading before considering live deployment. The creators are not responsible for any financial losses incurred.

---

Feel free to open issues or contribute if you have suggestions or encounter problems!