"""
Market Data Collector (Agent 1)
Fetches live market data (OHLCV) from NSE public APIs.
"""

import json
import time
import http.cookiejar
import urllib.request
import urllib.parse
import csv
import io
from datetime import datetime, timedelta

class MarketDataCollector:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
        }
        self._initialize_session()
        self.equity_list = []
        self._price_cache = {}
        self._cache_timestamp = 0.0

    def _initialize_session(self):
        """Initializes the NSE session to get the required cookies."""
        try:
            req = urllib.request.Request("https://www.nseindia.com", headers=self.headers)
            self.opener.open(req, timeout=10)
        except Exception as e:
            print(f"[Market Data] Failed to initialize NSE session: {e}")

    def fetch_nse_equity_list(self) -> list:
        """
        Dynamically fetches the complete list of all NSE listed equities.
        Returns a list of dicts: [{"symbol": "RELIANCE", "name": "Reliance Industries..."}, ...]
        """
        if self.equity_list:
            return self.equity_list

        print("[Market Data] Fetching complete NSE equity list...")
        try:
            url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(content))
                equities = []
                for row in reader:
                    equities.append({
                        "symbol": row["SYMBOL"],
                        "name": row["NAME OF COMPANY"]
                    })
                self.equity_list = equities
                print(f"[Market Data] Loaded {len(self.equity_list)} equities.")
                return self.equity_list
        except Exception as e:
            print(f"[Market Data] Error fetching equity list: {e}")
            # Fallback for testing if NSE blocks
            return [{"symbol": "RELIANCE", "name": "Reliance"}]
            
    def _refresh_price_cache(self):
        """Bulk-fetches live prices for 200+ NSE stocks (NIFTY + FO)."""
        now = time.time()
        if (now - self._cache_timestamp) < 20 and self._price_cache:
            return

        all_prices = {}
        for key in ["NIFTY", "FO"]:
            try:
                url = f"https://www.nseindia.com/api/market-data-pre-open?key={key}"
                req = urllib.request.Request(url, headers=self.api_headers)
                resp = self.opener.open(req, timeout=10)
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("data", []):
                    meta = item.get("metadata", {})
                    symbol = meta.get("symbol", "")
                    if symbol:
                        all_prices[symbol] = {
                            "lastPrice": meta.get("lastPrice", 0.0),
                            "change": meta.get("change", 0.0),
                            "pChange": meta.get("pChange", 0.0),
                            "previousClose": meta.get("previousClose", 0.0),
                            "yearHigh": meta.get("yearHigh", 0.0),
                            "yearLow": meta.get("yearLow", 0.0),
                            "volume": 0 # Pre-open API doesn't have volume, will be filled in quote
                        }
            except Exception as e:
                # Need to refresh session sometimes
                self._initialize_session()
                print(f"[Market Data] NSE API fetch error ({key}): {e}")

        self._price_cache = all_prices
        self._cache_timestamp = now

    def fetch_stock_quote(self, symbol: str) -> dict:
        """
        Fetches real-time quote (LTP, OHLC, volume) for a specific stock.
        """
        symbol = symbol.upper()
        # For simplicity and reliability in this agentic version, we'll try Yahoo Finance (yfinance API format but raw request)
        # Since yfinance library has issues, we use yahoo finance public API
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}.NS?range=1d&interval=1m"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                result = data['chart']['result'][0]
                meta = result['meta']
                indicators = result['indicators']['quote'][0]
                
                # Get latest valid data point
                close_prices = indicators.get('close', [])
                valid_closes = [c for c in close_prices if c is not None]
                
                if not valid_closes:
                    return None
                    
                latest_price = valid_closes[-1]
                high = max([h for h in indicators.get('high', []) if h is not None] or [latest_price])
                low = min([l for l in indicators.get('low', []) if l is not None] or [latest_price])
                volumes = [v for v in indicators.get('volume', []) if v is not None]
                volume = sum(volumes)
                prev_close = meta.get('chartPreviousClose', latest_price)

                return {
                    "price": round(latest_price, 2),
                    "day_high": round(high, 2),
                    "day_low": round(low, 2),
                    "prev_close": round(prev_close, 2),
                    "volume": volume
                }
        except Exception as e:
            # Fallback to NSE Cache
            self._refresh_price_cache()
            cached = self._price_cache.get(symbol)
            if cached and cached.get("lastPrice", 0) > 0:
                price = cached["lastPrice"]
                prev_close = cached.get("previousClose", 0.0)
                return {
                    "price": round(float(price), 2),
                    "day_high": round(float(price), 2),
                    "day_low": round(float(price), 2),
                    "prev_close": round(float(prev_close), 2),
                    "volume": 0,
                }
            print(f"[Market Data] Quote fetch failed for {symbol}: {e}")
            return None

    def fetch_stock_history(self, symbol: str, days: int = 20) -> list:
        """
        Fetches historical daily OHLCV data for technical analysis.
        Returns list of dicts: [{"date": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...}, ...]
        """
        symbol = symbol.upper()
        try:
            # Yahoo Finance daily history
            # 30 days is safe to cover 20 trading days
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}.NS?range=30d&interval=1d"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                quote = result['indicators']['quote'][0]
                
                history = []
                for i in range(len(timestamps)):
                    if quote['close'][i] is not None:
                        history.append({
                            "date": timestamps[i],
                            "open": quote['open'][i],
                            "high": quote['high'][i],
                            "low": quote['low'][i],
                            "close": quote['close'][i],
                            "volume": quote['volume'][i]
                        })
                
                # Return last 'days' records
                return history[-days:]
        except Exception as e:
            print(f"[Market Data] History fetch failed for {symbol}: {e}")
            return []

if __name__ == "__main__":
    md = MarketDataCollector()
    eq = md.fetch_nse_equity_list()
    print(f"Loaded {len(eq)} equities. Example: {eq[0] if eq else None}")
    quote = md.fetch_stock_quote("RELIANCE")
    print(f"RELIANCE Quote: {quote}")
    history = md.fetch_stock_history("RELIANCE", 5)
    print(f"RELIANCE 5-day History: {history}")
