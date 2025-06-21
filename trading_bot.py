import pandas as pd
import numpy as np
import ccxt
import talib
from datetime import datetime, timedelta
import time
import requests
import json
import logging
from typing import Dict, List, Tuple, Optional
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class TradingConfig:
    """Trading configuration parameters"""
    leverage: int = 5
    base_capital: float = 100.0
    rsi_period: int = 14
    rsi_buy_threshold: float = 40.0
    rsi_sell_threshold: float = 60.0
    rsi_exit_long: float = 50.0
    rsi_exit_short: float = 50.0
    ema_period: int = 200
    adx_period: int = 14
    adx_threshold: float = 20.0
    atr_period: int = 14
    atr_multiplier: float = 2.0
    breakout_period: int = 20
    timeframes: List[str] = None
    
    def __post_init__(self):
        if self.timeframes is None:
            self.timeframes = ['15m', '30m', '1h', '4h']

class TelegramBot:
    """Telegram bot for sending trading signals"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str) -> bool:
        """Send message to Telegram chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_signal(self, signal_type: str, symbol: str, price: float, 
                   strategy_type: str, additional_info: str = "") -> bool:
        """Send formatted trading signal"""
        emoji = "🟢" if signal_type.upper() == "BUY" else "🔴"
        message = f"""
{emoji} <b>TRADING SIGNAL</b> {emoji}

📊 <b>Symbol:</b> {symbol}
🎯 <b>Action:</b> {signal_type.upper()}
💰 <b>Price:</b> ${price:.4f}
⚡ <b>Strategy:</b> {strategy_type}
📈 <b>Timeframe:</b> Multiple TF Analysis

{additional_info}

🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
        """
        return self.send_message(message.strip())

class MTFTradingStrategy:
    """Multi-timeframe trading strategy based on Pine Script"""
    
    def __init__(self, config: TradingConfig, telegram_bot: TelegramBot):
        self.config = config
        self.telegram_bot = telegram_bot
        self.exchange = None
        self.last_signals = {}
        self.position_info = {
            'last_type': 'None',
            'last_dir': 'None',
            'entry_price': 0.0,
            'position_size': 0.0
        }
    
    def setup_exchange(self, exchange_name: str = 'binance', 
                      api_key: str = None, secret: str = None, 
                      sandbox: bool = True):
        """Initialize exchange connection"""
        try:
            exchange_class = getattr(ccxt, exchange_name)
            self.exchange = exchange_class({
                'apiKey': api_key,
                'secret': secret,
                'sandbox': sandbox,
                'enableRateLimit': True,
            })
            logging.info(f"Connected to {exchange_name} exchange")
        except Exception as e:
            logging.error(f"Failed to connect to exchange: {e}")
            raise
    
    def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Fetch OHLCV data from exchange"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logging.error(f"Failed to fetch OHLCV data: {e}")
            return pd.DataFrame()
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate EMA using talib"""
        return talib.EMA(data.values, timeperiod=period)
    
    def calculate_rsi(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate RSI using talib"""
        return talib.RSI(data.values, timeperiod=period)
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate ADX using talib"""
        return talib.ADX(high.values, low.values, close.values, timeperiod=period)
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate ATR using talib"""
        return talib.ATR(high.values, low.values, close.values, timeperiod=period)
    
    def get_mtf_emas(self, symbol: str) -> Dict[str, float]:
        """Get EMA values for all timeframes"""
        emas = {}
        for tf in self.config.timeframes:
            try:
                df = self.get_ohlcv_data(symbol, tf, limit=250)
                if not df.empty:
                    ema = self.calculate_ema(df['close'], self.config.ema_period)
                    emas[tf] = ema[-1] if not np.isnan(ema[-1]) else 0
                else:
                    emas[tf] = 0
            except Exception as e:
                logging.error(f"Error calculating EMA for {tf}: {e}")
                emas[tf] = 0
        return emas
    
    def analyze_market_regime(self, symbol: str) -> Tuple[bool, bool, Dict]:
        """Analyze market regime (trending vs ranging)"""
        try:
            # Get 1h and 4h data for ADX
            df_1h = self.get_ohlcv_data(symbol, '1h', limit=50)
            df_4h = self.get_ohlcv_data(symbol, '4h', limit=50)
            
            adx_1h = self.calculate_adx(df_1h['high'], df_1h['low'], df_1h['close'], self.config.adx_period)
            adx_4h = self.calculate_adx(df_4h['high'], df_4h['low'], df_4h['close'], self.config.adx_period)
            
            is_trending = (adx_1h[-1] > self.config.adx_threshold and 
                          adx_4h[-1] > self.config.adx_threshold)
            is_ranging = not is_trending
            
            regime_info = {
                'adx_1h': adx_1h[-1],
                'adx_4h': adx_4h[-1],
                'is_trending': is_trending,
                'is_ranging': is_ranging
            }
            
            return is_trending, is_ranging, regime_info
            
        except Exception as e:
            logging.error(f"Error analyzing market regime: {e}")
            return False, True, {}
    
    def check_trend_alignment(self, symbol: str, current_price: float) -> Tuple[bool, bool, str]:
        """Check if price is above/below all EMAs"""
        emas = self.get_mtf_emas(symbol)
        
        price_above_all = all(current_price > ema for ema in emas.values() if ema > 0)
        price_below_all = all(current_price < ema for ema in emas.values() if ema > 0)
        
        if price_above_all:
            bias = "BULLISH"
        elif price_below_all:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
        
        return price_above_all, price_below_all, bias
    
    def check_volatility_filter(self, symbol: str, timeframe: str = '1h') -> Tuple[bool, float]:
        """Check if there's enough volatility for trading"""
        try:
            df = self.get_ohlcv_data(symbol, timeframe, limit=100)
            atr = self.calculate_atr(df['high'], df['low'], df['close'], self.config.atr_period)
            atr_sma = talib.SMA(atr, timeperiod=50)
            
            current_atr = atr[-1]
            avg_atr = atr_sma[-1]
            
            enough_volatility = current_atr > avg_atr
            
            return enough_volatility, current_atr
            
        except Exception as e:
            logging.error(f"Error checking volatility: {e}")
            return False, 0.0
    
    def check_rsi_signals(self, symbol: str, timeframe: str = '1h') -> Dict:
        """Check RSI-based signals"""
        try:
            df = self.get_ohlcv_data(symbol, timeframe, limit=100)
            rsi = self.calculate_rsi(df['close'], self.config.rsi_period)
            current_rsi = rsi[-1]
            
            return {
                'rsi': current_rsi,
                'rsi_buy': current_rsi < self.config.rsi_buy_threshold,
                'rsi_sell': current_rsi > self.config.rsi_sell_threshold,
                'rsi_exit_long': current_rsi > self.config.rsi_exit_long,
                'rsi_exit_short': current_rsi < self.config.rsi_exit_short
            }
            
        except Exception as e:
            logging.error(f"Error checking RSI signals: {e}")
            return {}
    
    def check_breakout_signals(self, symbol: str, timeframe: str = '1h') -> Dict:
        """Check breakout signals"""
        try:
            df = self.get_ohlcv_data(symbol, timeframe, limit=self.config.breakout_period + 10)
            
            # Calculate highest high and lowest low of previous 20 periods
            highest_break = df['close'].shift(1).rolling(window=self.config.breakout_period).max().iloc[-1]
            lowest_break = df['close'].shift(1).rolling(window=self.config.breakout_period).min().iloc[-1]
            
            current_price = df['close'].iloc[-1]
            
            return {
                'long_break': current_price > highest_break,
                'short_break': current_price < lowest_break,
                'highest_break': highest_break,
                'lowest_break': lowest_break
            }
            
        except Exception as e:
            logging.error(f"Error checking breakout signals: {e}")
            return {}
    
    def generate_signals(self, symbol: str) -> List[Dict]:
        """Main signal generation logic"""
        signals = []
        
        try:
            # Get current price
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Market regime analysis
            is_trending, is_ranging, regime_info = self.analyze_market_regime(symbol)
            
            # Trend alignment
            price_above_all, price_below_all, bias = self.check_trend_alignment(symbol, current_price)
            
            # Volatility filter
            enough_volatility, current_atr = self.check_volatility_filter(symbol)
            
            # RSI analysis
            rsi_signals = self.check_rsi_signals(symbol)
            
            # Breakout analysis
            breakout_signals = self.check_breakout_signals(symbol)
            
            # Generate RSI signals (for ranging markets)
            if (is_ranging and enough_volatility and rsi_signals):
                if (rsi_signals.get('rsi_buy', False) and price_above_all):
                    signals.append({
                        'type': 'BUY',
                        'strategy': 'RSI Mean Reversion',
                        'symbol': symbol,
                        'price': current_price,
                        'rsi': rsi_signals['rsi'],
                        'regime': 'RANGING',
                        'bias': bias,
                        'confidence': 'HIGH' if rsi_signals['rsi'] < 35 else 'MEDIUM'
                    })
                
                if (rsi_signals.get('rsi_sell', False) and price_below_all):
                    signals.append({
                        'type': 'SELL',
                        'strategy': 'RSI Mean Reversion',
                        'symbol': symbol,
                        'price': current_price,
                        'rsi': rsi_signals['rsi'],
                        'regime': 'RANGING',
                        'bias': bias,
                        'confidence': 'HIGH' if rsi_signals['rsi'] > 65 else 'MEDIUM'
                    })
            
            # Generate breakout signals (for trending markets)
            if (is_trending and enough_volatility and breakout_signals):
                if (breakout_signals.get('long_break', False) and price_above_all):
                    signals.append({
                        'type': 'BUY',
                        'strategy': 'Breakout',
                        'symbol': symbol,
                        'price': current_price,
                        'breakout_level': breakout_signals['highest_break'],
                        'regime': 'TRENDING',
                        'bias': bias,
                        'confidence': 'HIGH'
                    })
                
                if (breakout_signals.get('short_break', False) and price_below_all):
                    signals.append({
                        'type': 'SELL',
                        'strategy': 'Breakout',
                        'symbol': symbol,
                        'price': current_price,
                        'breakout_level': breakout_signals['lowest_break'],
                        'regime': 'TRENDING',
                        'bias': bias,
                        'confidence': 'HIGH'
                    })
            
            # Log market state
            logging.info(f"Market Analysis - {symbol}: Regime={regime_info.get('is_trending', False)}, "
                        f"Bias={bias}, RSI={rsi_signals.get('rsi', 0):.2f}, "
                        f"Volatility={enough_volatility}")
            
        except Exception as e:
            logging.error(f"Error generating signals: {e}")
        
        return signals
    
    def send_signal_to_telegram(self, signal: Dict) -> bool:
        """Send signal to Telegram with formatted message"""
        try:
            additional_info = ""
            
            if signal['strategy'] == 'RSI Mean Reversion':
                additional_info = f"📊 RSI: {signal.get('rsi', 0):.2f}\n🎯 Confidence: {signal.get('confidence', 'MEDIUM')}"
            elif signal['strategy'] == 'Breakout':
                level = signal.get('breakout_level', 0)
                additional_info = f"📈 Breakout Level: ${level:.4f}\n🎯 Confidence: {signal.get('confidence', 'HIGH')}"
            
            additional_info += f"\n📊 Market Regime: {signal.get('regime', 'UNKNOWN')}"
            additional_info += f"\n📈 Bias: {signal.get('bias', 'NEUTRAL')}"
            
            return self.telegram_bot.send_signal(
                signal_type=signal['type'],
                symbol=signal['symbol'],
                price=signal['price'],
                strategy_type=signal['strategy'],
                additional_info=additional_info
            )
        except Exception as e:
            logging.error(f"Error sending signal to Telegram: {e}")
            return False
    
    def run_strategy(self, symbols: List[str], check_interval: int = 300):
        """Main strategy execution loop"""
        logging.info(f"Starting strategy for symbols: {symbols}")
        
        while True:
            try:
                for symbol in symbols:
                    logging.info(f"Analyzing {symbol}...")
                    
                    signals = self.generate_signals(symbol)
                    
                    for signal in signals:
                        # Check if we already sent this signal recently
                        signal_key = f"{symbol}_{signal['type']}_{signal['strategy']}"
                        current_time = datetime.now()
                        
                        if (signal_key not in self.last_signals or 
                            (current_time - self.last_signals[signal_key]).seconds > 3600):  # 1 hour cooldown
                            
                            if self.send_signal_to_telegram(signal):
                                self.last_signals[signal_key] = current_time
                                logging.info(f"Signal sent: {signal['type']} {symbol} at {signal['price']}")
                            else:
                                logging.error(f"Failed to send signal: {signal}")
                
                logging.info(f"Sleeping for {check_interval} seconds...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logging.info("Strategy stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in strategy loop: {e}")
                time.sleep(60)  # Wait before retrying

def main():
    """Main execution function"""
    # Configuration
    config = TradingConfig(
        leverage=5,
        base_capital=100.0,
        rsi_buy_threshold=40.0,
        rsi_sell_threshold=60.0,
        adx_threshold=20.0
    )
    
    # Environment variables (set these in your environment or GitHub secrets)
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')
    EXCHANGE_API_KEY = os.getenv('EXCHANGE_API_KEY', '')
    EXCHANGE_SECRET = os.getenv('EXCHANGE_SECRET', '')
    
    # Initialize Telegram bot
    telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Initialize strategy
    strategy = MTFTradingStrategy(config, telegram_bot)
    
    # Setup exchange (using testnet/sandbox for safety)
    strategy.setup_exchange('binance', EXCHANGE_API_KEY, EXCHANGE_SECRET, sandbox=True)
    
    # Symbols to monitor
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    # Send startup message
    telegram_bot.send_message("🤖 <b>Trading Bot Started</b>\n\n"
                             f"📊 Monitoring: {', '.join(symbols)}\n"
                             f"⚡ Strategy: MTF Hybrid (RSI + Breakout)\n"
                             f"🕐 Check Interval: 5 minutes")
    
    # Run strategy
    strategy.run_strategy(symbols, check_interval=300)  # Check every 5 minutes

if __name__ == "__main__":
    main()