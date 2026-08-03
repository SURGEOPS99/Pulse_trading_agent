"""
Risk Management & Order Calculator Engine (Agent 5).
Dynamically computes position sizing based on available capital, risk level, and ATR.
Computes Stop-Loss based on ATR (1.5x) and sets dynamic Trigger/Limit prices.
Formats clean, mobile-optimized HTML cards for Telegram.
"""

import math
from config import BASE_CAPITAL, MIS_LEVERAGE, TRIGGER_BUFFER_PCT, LIMIT_SLIPPAGE_BUFFER, ATR_SL_MULTIPLIER

class OrderCalculator:
    def __init__(self, base_capital: float = BASE_CAPITAL, max_leverage: float = MIS_LEVERAGE):
        self.base_capital = base_capital
        self.max_leverage = max_leverage

    def compute_breakout_order(self, signal: dict, custom_capital: float = None) -> dict:
        """
        Calculates exact quantity, trigger price, limit price, stop loss, and risk metrics.
        Uses ATR for dynamic Stop Loss. Uses Risk Rating for dynamic Leverage/Position Sizing.
        """
        symbol = signal["symbol"]
        tech_data = signal["technical_data"]
        risk_level = signal["risk_level"]
        
        current_price = tech_data["current_price"]
        resistance_price = tech_data["resistance"]
        atr = tech_data["atr"]

        capital = custom_capital if custom_capital is not None else self.base_capital
        
        # 1. Dynamic Leverage based on Risk Level (Capital Guard)
        # LOW Risk = 5x, MEDIUM Risk = 3x, HIGH Risk = 1.5x
        applied_leverage = self.max_leverage
        if risk_level == "HIGH":
            applied_leverage = max(1.5, self.max_leverage * 0.3)
        elif risk_level == "MEDIUM":
            applied_leverage = max(3.0, self.max_leverage * 0.6)
            
        effective_cap = capital * applied_leverage
        
        # Max 40% of effective capital on a single position to prevent concentration
        max_position_size = effective_cap * 0.40

        # 2. Trigger Price: 0.1% or ₹0.10 buffer above dynamic resistance
        buffer = max(0.10, round(resistance_price * TRIGGER_BUFFER_PCT, 2))
        trigger_price = round(max(resistance_price, current_price) + buffer, 2)

        # 3. Limit Price: ₹0.10 or 0.1% slippage cap above Trigger Price
        limit_price = round(trigger_price + max(LIMIT_SLIPPAGE_BUFFER, round(trigger_price * 0.001, 2)), 2)
        
        # 4. Stop Loss: 1.5x ATR below entry
        sl_distance = max(atr * ATR_SL_MULTIPLIER, trigger_price * 0.005) # Min 0.5% SL
        stop_loss = round(trigger_price - sl_distance, 2)

        # 5. Quantity: Position size calculated from allocated purchasing power
        quantity = max(1, math.floor(max_position_size / limit_price))
        total_exposure = round(quantity * limit_price, 2)
        margin_required = round(total_exposure / applied_leverage, 2)

        # Emoji mapping
        emoji = "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"

        return {
            "symbol": symbol.upper(),
            "exchange": "NSE",
            "tab": "Regular",
            "product": "Intraday",
            "quantity": quantity,
            "stoploss_switch": "ON",
            "current_price": current_price,
            "resistance_price": resistance_price,
            "trigger_price": f"{trigger_price:.2f}",
            "limit_price": f"{limit_price:.2f}",
            "stop_loss": f"{stop_loss:.2f}",
            "base_capital": capital,
            "effective_capital": effective_cap,
            "total_exposure": total_exposure,
            "margin_required": margin_required,
            "leverage": f"{applied_leverage:g}x",
            "risk_level": risk_level,
            "risk_emoji": emoji,
            "composite_score": signal["composite_score"],
            "headlines": signal.get("headlines", [])
        }

    def generate_telegram_message(self, order: dict) -> str:
        """
        Formats breakout order into a clean, mobile-optimized HTML card for Telegram.
        """
        headlines_text = ""
        for hl in order["headlines"][:2]: # Show top 2 headlines
            headlines_text += f"\n📰 <i>{hl['title']} [{hl['source']}]</i>"
        if not headlines_text:
            headlines_text = "\n📈 <i>Strong Technical Breakout detected</i>"
            
        msg = (
            f"🚀 <b>MULTI-FACTOR BREAKOUT ALERT</b>\n"
            f"📈 <b>Ticker:</b> <code>{order['symbol']}</code> ({order['exchange']})\n"
            f"⚠️ <b>Risk Level:</b> <b>{order['risk_level']} RISK {order['risk_emoji']}</b> (Score: {order['composite_score']})\n"
            f"{headlines_text}\n\n"
            f"<b>ORDER DETAILS:</b>\n"
            f"• <b>Product:</b> <code>{order['product']}</code> (Allocated Leverage: {order['leverage']})\n"
            f"• <b>Quantity:</b> <code>{order['quantity']}</code>\n"
            f"• <b>Trigger Price:</b> <code>₹{order['trigger_price']}</code> (Entry)\n"
            f"• <b>Limit Price:</b> <code>₹{order['limit_price']}</code> (Max slippage)\n"
            f"• <b>Stop Loss:</b> <code>₹{order['stop_loss']}</code> (Dynamic ATR)\n\n"
            f"📋 <b>EXECUTION CARD:</b>\n"
            f"<pre>"
            f"Field           Value\n"
            f"-------------------------------\n"
            f"Exchange      : {order['exchange']}\n"
            f"Product       : {order['product']}\n"
            f"Quantity      : {order['quantity']}\n"
            f"Trigger Price : Rs {order['trigger_price']}\n"
            f"Limit Price   : Rs {order['limit_price']}\n"
            f"Stop Loss     : Rs {order['stop_loss']}\n"
            f"</pre>\n"
            f"⚡ <b>Margin Required:</b> ₹{order['margin_required']:,.2f} <i>(Exposure: ₹{order['total_exposure']:,.2f})</i>"
        )
        return msg

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    calc = OrderCalculator()
    
    # Mock signal
    signal = {
        "symbol": "TATAMOTORS",
        "composite_score": 0.82,
        "risk_level": "LOW",
        "technical_data": {
            "current_price": 990.50,
            "resistance": 992.00,
            "atr": 18.5
        },
        "headlines": [{"title": "Tata Motors EV sales jump 28%", "source": "ET"}]
    }
    
    order = calc.compute_breakout_order(signal)
    print(calc.generate_telegram_message(order))
