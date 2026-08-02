"""
Configuration parameters for Autonomous NSE Intraday Stock Monitor and Telegram Alert Agent.
"""

import os

# Account & Risk Capital Parameters
BASE_CAPITAL = 2524.10          # Available capital balance in INR (₹)
MIS_LEVERAGE = 5.0              # Intraday (MIS) leverage multiplier (5x)
EFFECTIVE_CAPITAL = BASE_CAPITAL * MIS_LEVERAGE  # Total purchasing power: ₹12,620.50

# Strategy & Signal Thresholds
SENTIMENT_THRESHOLD = 0.40      # Minimum NLP sentiment score for bullish catalyst (0.0 to 1.0)
TRIGGER_BUFFER_PCT = 0.0010     # 0.1% buffer above resistance level for Trigger Price
LIMIT_SLIPPAGE_BUFFER = 0.10     # ₹0.10 or 0.1% slippage allowance for SL-Limit Order

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8815412040:AAH4iB1rFPWnmpEnQFkvQ2aUMq6hNtxqGxA")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8313018138")

# Comprehensive NSE Companies Watchlist (Nifty 50, Nifty Next 50, Midcaps & High-Beta Intraday Tickers)
NSE_COMPANIES_DATABASE = [
    # NIFTY 50 & MAJOR BLUECHIPS
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd.", "sector": "Energy", "base_price": 2980.50, "resistance": 3000.00},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd.", "sector": "Auto", "base_price": 985.40, "resistance": 992.00},
    {"symbol": "INFY", "name": "Infosys Ltd.", "sector": "IT", "base_price": 1820.00, "resistance": 1835.00},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd.", "sector": "IT", "base_price": 4250.00, "resistance": 4280.00},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd.", "sector": "Banking", "base_price": 1640.00, "resistance": 1655.00},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd.", "sector": "Banking", "base_price": 1210.00, "resistance": 1225.00},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking", "base_price": 845.20, "resistance": 852.00},
    {"symbol": "AXISBANK", "name": "Axis Bank Ltd.", "sector": "Banking", "base_price": 1150.00, "resistance": 1165.00},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd.", "sector": "Banking", "base_price": 1780.00, "resistance": 1795.00},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd.", "sector": "Telecom", "base_price": 1480.00, "resistance": 1495.00},
    {"symbol": "ITC", "name": "ITC Ltd.", "sector": "FMCG", "base_price": 490.00, "resistance": 496.00},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd.", "sector": "Infra", "base_price": 3620.00, "resistance": 3650.00},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries", "sector": "Pharma", "base_price": 1710.00, "resistance": 1725.00},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd.", "sector": "Auto", "base_price": 12400.00, "resistance": 12500.00},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd.", "sector": "Finance", "base_price": 6850.00, "resistance": 6920.00},
    {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd.", "sector": "Consumer", "base_price": 2980.00, "resistance": 3010.00},
    {"symbol": "HCLTECH", "name": "HCL Technologies Ltd.", "sector": "IT", "base_price": 1580.00, "resistance": 1595.00},
    {"symbol": "TITAN", "name": "Titan Company Ltd.", "sector": "Consumer", "base_price": 3450.00, "resistance": 3480.00},
    {"symbol": "WIPRO", "name": "Wipro Ltd.", "sector": "IT", "base_price": 520.00, "resistance": 526.00},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement Ltd.", "sector": "Cement", "base_price": 11200.00, "resistance": 11300.00},
    {"symbol": "NTPC", "name": "NTPC Ltd.", "sector": "Power", "base_price": 410.00, "resistance": 415.00},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corporation", "sector": "Energy", "base_price": 325.00, "resistance": 330.00},
    {"symbol": "POWERGRID", "name": "Power Grid Corporation of India", "sector": "Power", "base_price": 345.00, "resistance": 350.00},
    {"symbol": "COALINDIA", "name": "Coal India Ltd.", "sector": "Mining", "base_price": 510.00, "resistance": 516.00},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Ltd.", "sector": "Auto", "base_price": 2920.00, "resistance": 2950.00},
    {"symbol": "TATASTEEL", "name": "Tata Steel Ltd.", "sector": "Metals", "base_price": 165.30, "resistance": 167.50},
    {"symbol": "JSWSTEEL", "name": "JSW Steel Ltd.", "sector": "Metals", "base_price": 930.00, "resistance": 940.00},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Ltd.", "sector": "Metals/Infra", "base_price": 3150.00, "resistance": 3180.00},
    {"symbol": "ADANIPORTS", "name": "Adani Ports & SEZ Ltd.", "sector": "Ports", "base_price": 1490.00, "resistance": 1510.00},
    {"symbol": "GRASIM", "name": "Grasim Industries Ltd.", "sector": "Cement", "base_price": 2720.00, "resistance": 2745.00},
    {"symbol": "TECHM", "name": "Tech Mahindra Ltd.", "sector": "IT", "base_price": 1480.00, "resistance": 1495.00},

    # HIGH BETA, MIDCAP & POPULAR INTRADAY STOCKS
    {"symbol": "ZOMATO", "name": "Zomato Ltd.", "sector": "Tech/Consumer", "base_price": 242.10, "resistance": 245.50},
    {"symbol": "SJVN", "name": "SJVN Limited", "sector": "Power", "base_price": 94.80, "resistance": 95.40},
    {"symbol": "SUZLON", "name": "Suzlon Energy Ltd.", "sector": "Clean Energy", "base_price": 68.50, "resistance": 69.80},
    {"symbol": "RVNL", "name": "Rail Vikas Nigam Ltd.", "sector": "Railways", "base_price": 580.00, "resistance": 588.00},
    {"symbol": "IRCTC", "name": "Indian Railway Catering & Tourism", "sector": "Railways", "base_price": 1020.00, "resistance": 1032.00},
    {"symbol": "IRFC", "name": "Indian Railway Finance Corporation", "sector": "Railways", "base_price": 205.00, "resistance": 208.50},
    {"symbol": "BEL", "name": "Bharat Electronics Ltd.", "sector": "Defense", "base_price": 315.00, "resistance": 320.00},
    {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd.", "sector": "Defense", "base_price": 4900.00, "resistance": 4950.00},
    {"symbol": "BHEL", "name": "Bharat Heavy Electricals Ltd.", "sector": "Capital Goods", "base_price": 310.00, "resistance": 315.00},
    {"symbol": "DLF", "name": "DLF Ltd.", "sector": "Realty", "base_price": 860.00, "resistance": 870.00},
    {"symbol": "TATAPOWER", "name": "Tata Power Company Ltd.", "sector": "Power", "base_price": 440.00, "resistance": 446.00},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products Ltd.", "sector": "FMCG", "base_price": 1210.00, "resistance": 1222.00},
    {"symbol": "HINDALCO", "name": "Hindalco Industries Ltd.", "sector": "Metals", "base_price": 660.00, "resistance": 668.00},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corporation Ltd.", "sector": "Energy", "base_price": 350.00, "resistance": 355.00},
    {"symbol": "IOC", "name": "Indian Oil Corporation Ltd.", "sector": "Energy", "base_price": 175.00, "resistance": 178.00},
    {"symbol": "INDIGO", "name": "InterGlobe Aviation Ltd.", "sector": "Aviation", "base_price": 4350.00, "resistance": 4400.00},
    {"symbol": "POLYCAB", "name": "Polycab India Ltd.", "sector": "Electricals", "base_price": 6800.00, "resistance": 6880.00},
    {"symbol": "TRENT", "name": "Trent Ltd.", "sector": "Retail", "base_price": 6250.00, "resistance": 6320.00},
]

# Market Operating Hours (IST)
MARKET_OPEN_TIME = "09:15"
MARKET_CLOSE_TIME = "15:30"
