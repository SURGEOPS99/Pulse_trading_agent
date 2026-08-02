"""
Risk Management & Order Calculator Engine.
Dynamically computes position sizing based on available capital (₹2,524.10) and 5x MIS leverage.
Computes Trigger Price (0.1% buffer above resistance) and Limit Price (max allowable execution slippage).
Calculates Risk Levels ('LOW', 'MEDIUM', 'HIGH') based on catalyst conviction & sentiment score.
Formats clean, mobile-optimized HTML cards for Telegram.
"""

import math
from config import BASE_CAPITAL, MIS_LEVERAGE, TRIGGER_BUFFER_PCT, LIMIT_SLIPPAGE_BUFFER

class OrderCalculator:
    """
    Computes precise intraday Stop-Loss Limit orders and risk levels for NSE stocks.
    """

    def __init__(self, base_capital: float = BASE_CAPITAL, leverage: float = MIS_LEVERAGE):
        self.base_capital = base_capital
        self.leverage = leverage
        self.effective_capital = self.base_capital * self.leverage

    def compute_risk_rating(self, sentiment_score: float) -> dict:
        """
        Maps NLP sentiment score to risk rating levels: LOW, MEDIUM, or HIGH risk.
        - Score >= 0.70: LOW Risk (Strong fundamental catalyst / earnings / major order win)
        - Score 0.50 - 0.69: MEDIUM Risk (Moderate momentum / steady breakout)
        - Score < 0.50: HIGH Risk (Speculative volatility breakout)
        """
        if sentiment_score >= 0.70:
            return {"level": "LOW", "full": "LOW RISK 🟢", "emoji": "🟢", "desc": "Strong Catalyst Conviction"}
        elif sentiment_score >= 0.50:
            return {"level": "MEDIUM", "full": "MEDIUM RISK 🟡", "emoji": "🟡", "desc": "Moderate Breakout Momentum"}
        else:
            return {"level": "HIGH", "full": "HIGH RISK 🔴", "emoji": "🔴", "desc": "Speculative Volatility"}

    def compute_breakout_order(self, symbol: str, resistance_price: float, custom_capital: float = None) -> dict:
        """
        Calculates exact quantity, trigger price, limit price, and risk metrics for a breakout order.
        """
        if not symbol or resistance_price <= 0:
            raise ValueError(f"Invalid stock parameter: symbol={symbol}, resistance_price={resistance_price}")

        capital = custom_capital if custom_capital is not None else self.base_capital
        effective_cap = capital * self.leverage

        # 1. Trigger Price: 0.1% or ₹0.10 buffer above resistance level
        buffer = max(0.10, round(resistance_price * TRIGGER_BUFFER_PCT, 2))
        trigger_price = round(resistance_price + buffer, 2)

        # 2. Limit Price: ₹0.10 or 0.1% slippage cap above Trigger Price
        limit_price = round(trigger_price + max(0.10, round(trigger_price * 0.001, 2)), 2)

        # 3. Quantity: Position size calculated from effective purchasing power (MIS 5x)
        quantity = max(1, math.floor(effective_cap / limit_price))
        total_exposure = round(quantity * limit_price, 2)
        margin_required = round(total_exposure / self.leverage, 2)

        return {
            "symbol": symbol.upper(),
            "exchange": "NSE",
            "tab": "Regular",
            "product": "Intraday",
            "quantity": quantity,
            "stoploss_switch": "ON (Toggled Right)",
            "resistance_price": resistance_price,
            "trigger_price": f"{trigger_price:.2f}",
            "limit_price": f"{limit_price:.2f}",
            "base_capital": capital,
            "effective_capital": effective_cap,
            "total_exposure": total_exposure,
            "margin_required": margin_required,
            "leverage": f"{self.leverage:g}x MIS"
        }

    def generate_telegram_message(self, order: dict) -> str:
        """
        Formats breakout order into a clean, mobile-optimized HTML card for Telegram
        with explicit LOW, MEDIUM, or HIGH risk ratings.
        """
        score = order.get("sentiment_score", 0.60)
        risk = self.compute_risk_rating(score)

        headline_text = f"\n📰 <i>Catalyst: {order['headline']}</i>\n" if order.get('headline') else ""
        
        msg = (
            f"🚀 <b>HIGH-CONFIDENCE BREAKOUT ORDER</b>\n"
            f"📈 <b>Ticker:</b> <code>{order['symbol']}</code> ({order['exchange']})\n"
            f"⚠️ <b>Risk Level:</b> <b>{risk['full']}</b> <i>({risk['desc']})</i>\n"
            f"{headline_text}\n"
            f"<b>ORDER DETAILS:</b>\n"
            f"• <b>Exchange:</b> <code>{order['exchange']}</code>\n"
            f"• <b>Tab:</b> <code>{order['tab']}</code>\n"
            f"• <b>Product:</b> <code>{order['product']}</code> (5x MIS Leverage)\n"
            f"• <b>Risk Rating:</b> <code>{risk['level']} RISK</code> {risk['emoji']}\n"
            f"• <b>Quantity:</b> <code>{order['quantity']}</code> (Position size for ₹{order['base_capital']:,.2f})\n"
            f"• <b>Stoploss Switch:</b> <code>{order['stoploss_switch']}</code>\n"
            f"• <b>Trigger Price:</b> <code>₹{order['trigger_price']}</code> (Activates order)\n"
            f"• <b>Limit Price:</b> <code>₹{order['limit_price']}</code> (Max execution price)\n\n"
            f"📋 <b>EXECUTION CARD:</b>\n"
            f"<pre>"
            f"Field           Value\n"
            f"-------------------------------\n"
            f"Exchange      : {order['exchange']}\n"
            f"Tab           : {order['tab']}\n"
            f"Product       : {order['product']} (MIS)\n"
            f"Risk Level    : {risk['level']} RISK\n"
            f"Quantity      : {order['quantity']}\n"
            f"SL Switch     : ON (Right)\n"
            f"Trigger Price : Rs {order['trigger_price']}\n"
            f"Limit Price   : Rs {order['limit_price']}\n"
            f"</pre>\n"
            f"⚡ <b>Margin Required:</b> ₹{order['margin_required']:,.2f} <i>(Exposure: ₹{order['total_exposure']:,.2f})</i>"
        )
        return msg

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    calc = OrderCalculator()
    order = calc.compute_breakout_order("TATAMOTORS", 992.00)
    order["sentiment_score"] = 0.76
    order["headline"] = "Tata Motors EV sales jump 28% YoY; stock tests breakout"
    print(calc.generate_telegram_message(order))
