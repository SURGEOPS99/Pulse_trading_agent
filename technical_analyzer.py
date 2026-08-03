"""
Technical Analyzer (Agent 3)
Computes technical indicators (SMA, RSI, VWAP, Support/Resistance, ATR, Volume)
from OHLCV data.
"""

import math
import json
from config import (
    SMA_FAST_PERIOD,
    SMA_SLOW_PERIOD,
    RSI_PERIOD,
    RSI_OVERSOLD,
    RSI_OVERBOUGHT,
    VOLUME_SURGE_MULTIPLIER,
    ATR_PERIOD
)

class TechnicalAnalyzer:
    def __init__(self):
        pass

    def _calculate_sma(self, prices: list, period: int) -> float:
        """Calculates Simple Moving Average."""
        if not prices or len(prices) < period:
            return 0.0
        return sum(prices[-period:]) / period

    def _calculate_rsi(self, prices: list, period: int = RSI_PERIOD) -> float:
        """Calculates Relative Strength Index."""
        if not prices or len(prices) <= period:
            return 50.0  # Default neutral

        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(change))
                
        # Simple moving average for initial RSI
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)

    def _calculate_vwap(self, history: list) -> float:
        """Calculates Volume-Weighted Average Price (simplified using daily data)."""
        if not history:
            return 0.0
            
        total_vp = 0.0
        total_vol = 0.0
        
        # Calculate over the last few days to represent near-term VWAP
        for day in history[-5:]: 
            typical_price = (day['high'] + day['low'] + day['close']) / 3
            total_vp += typical_price * day['volume']
            total_vol += day['volume']
            
        if total_vol == 0:
            return history[-1]['close'] if history else 0.0
            
        return round(total_vp / total_vol, 2)

    def _calculate_atr(self, history: list, period: int = ATR_PERIOD) -> float:
        """Calculates Average True Range."""
        if not history or len(history) <= 1:
            return 0.0
            
        true_ranges = []
        for i in range(1, len(history)):
            high = history[i]['high']
            low = history[i]['low']
            prev_close = history[i-1]['close']
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)
            
        if len(true_ranges) < period:
            period = len(true_ranges)
            
        if period == 0:
            return 0.0
            
        atr = sum(true_ranges[-period:]) / period
        return round(atr, 2)

    def _calculate_dynamic_levels(self, history: list) -> dict:
        """Calculates dynamic Support and Resistance from recent price action."""
        if not history:
            return {"support": 0.0, "resistance": 0.0}
            
        highs = [day['high'] for day in history]
        lows = [day['low'] for day in history]
        
        # Simple dynamic resistance: max high of last N days
        # Simple dynamic support: min low of last N days
        resistance = max(highs)
        support = min(lows)
        
        # If current price is at ATH, project a resistance level
        current_price = history[-1]['close']
        if current_price >= resistance:
            # Project resistance 1 ATR above current price
            atr = self._calculate_atr(history)
            resistance = current_price + max(atr, current_price * 0.02)
            
        return {
            "support": round(support, 2),
            "resistance": round(resistance, 2)
        }

    def analyze(self, symbol: str, history: list, current_quote: dict) -> dict:
        """
        Runs full technical analysis suite on a stock.
        Returns a dictionary with technical indicators and a composite technical score.
        """
        if not history or not current_quote:
            return None

        closes = [day['close'] for day in history]
        # Append current price to closes for up-to-date indicators
        current_price = current_quote['price']
        closes.append(current_price)
        
        # Calculate Indicators
        sma_fast = self._calculate_sma(closes, SMA_FAST_PERIOD)
        sma_slow = self._calculate_sma(closes, SMA_SLOW_PERIOD)
        rsi = self._calculate_rsi(closes)
        vwap = self._calculate_vwap(history)
        atr = self._calculate_atr(history)
        levels = self._calculate_dynamic_levels(history)
        
        # Volume Analysis
        volumes = [day['volume'] for day in history]
        avg_volume = sum(volumes) / len(volumes) if volumes else 1
        current_volume = current_quote['volume']
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        is_volume_surge = volume_ratio >= VOLUME_SURGE_MULTIPLIER

        # Scoring Logic (0.0 to 1.0)
        score = 0.0
        
        # 1. Trend (SMA Crossover) - 0.4 weight
        if sma_fast > sma_slow:
            score += 0.4
        elif current_price > sma_fast:
            score += 0.2
            
        # 2. Momentum (RSI) - 0.3 weight
        if 50 <= rsi <= RSI_OVERBOUGHT:
            score += 0.3  # Healthy bullish momentum
        elif rsi < RSI_OVERSOLD:
            score += 0.2  # Oversold bounce potential
        elif rsi > RSI_OVERBOUGHT:
            score += 0.1  # Overbought, risky
            
        # 3. Value (VWAP) - 0.3 weight
        if current_price > vwap:
            score += 0.3
            
        return {
            "symbol": symbol,
            "current_price": current_price,
            "sma_fast": round(sma_fast, 2),
            "sma_slow": round(sma_slow, 2),
            "rsi": rsi,
            "vwap": vwap,
            "atr": atr,
            "support": levels['support'],
            "resistance": levels['resistance'],
            "volume_ratio": round(volume_ratio, 2),
            "is_volume_surge": is_volume_surge,
            "technical_score": round(score, 2)
        }

if __name__ == "__main__":
    from market_data import MarketDataCollector
    md = MarketDataCollector()
    history = md.fetch_stock_history("RELIANCE", 20)
    quote = md.fetch_stock_quote("RELIANCE")
    
    if history and quote:
        ta = TechnicalAnalyzer()
        analysis = ta.analyze("RELIANCE", history, quote)
        print(f"Technical Analysis for RELIANCE:\n{json.dumps(analysis, indent=2)}")
    else:
        print("Could not fetch data for test.")
