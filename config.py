"""
Configuration parameters for the Intraday Trading Agent.
"""

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = "8815412040:AAH4iB1rFPWnmpEnQFkvQ2aUMq6hNtxqGxA"
TELEGRAM_CHAT_ID = "2140889242"

# Core Trading Configuration
BASE_CAPITAL = 25000.00
MIS_LEVERAGE = 5.0 # Max leverage

# Technical Analysis (Agent 3) Parameters
SMA_FAST_PERIOD = 9
SMA_SLOW_PERIOD = 21
RSI_PERIOD = 14
RSI_OVERSOLD = 40 # Slightly higher for intraday bounce
RSI_OVERBOUGHT = 70
VOLUME_SURGE_MULTIPLIER = 1.5 # 1.5x average volume
ATR_PERIOD = 14

# Signal Engine (Agent 4) Thresholds
SENTIMENT_THRESHOLD = 0.30

# Order Calculator (Agent 5) Parameters
TRIGGER_BUFFER_PCT = 0.001 # 0.1% buffer above resistance
LIMIT_SLIPPAGE_BUFFER = 0.10 # Max slippage cap (Rs)
ATR_SL_MULTIPLIER = 1.5 # Trailing SL based on ATR

# Price Monitor (Agent 6) Parameters
PRICE_CHECK_INTERVAL = 180  # Check open positions every 3 minutes
HIGH_ALERT_COOLDOWN = 1800  # Minimum 30 mins between "New High" alerts for same stock
HIGH_ALERT_MIN_JUMP_PCT = 0.005  # Need at least 0.5% jump for a new "New High" alert
TRAILING_SL_PCT = 0.015 # Drop of 1.5% from intraday high triggers sell alert

# Market Hours
MARKET_OPEN_TIME = "09:15"
MARKET_CLOSE_TIME = "15:30"
