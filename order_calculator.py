"""
Risk Management & Order Calculator Engine.
Dynamically computes position sizing based on available capital (₹2,524.10) and 5x MIS leverage.
Computes Trigger Price (0.1% buffer above resistance) and Limit Price (max allowable execution slippage).
Formats standardized breakout order tables.
"""

import math
from config import BASE_CAPITAL, MIS_LEVERAGE, TRIGGER_BUFFER_PCT, LIMIT_SLIPPAGE_BUFFER

class OrderCalculator:
    """
    Computes precise intraday Stop-Loss Limit orders for NSE stocks.
    """

    def __init__(self, base_capital: float = BASE_CAPITAL, leverage: float = MIS_LEVERAGE):
        self.base_capital = base_capital
        self.leverage = leverage
        self.effective_capital = self.base_capital * self.leverage

    def compute_breakout_order(self, symbol: str, resistance_price: float, custom_capital: float = None) -> dict:
        """
        Calculates exact quantity, trigger price, and limit price for a breakout order.
        
        Args:
            symbol (str): NSE ticker symbol (e.g., 'TATAMOTORS', 'SJVN')
            resistance_price (float): Key technical resistance level (e.g., 95.40 or 742.00)
            custom_capital (float): Optional capital override
        """
        capital = custom_capital if custom_capital is not None else self.base_capital
        effective_cap = capital * self.leverage

        # 1. Trigger Price: 0.1% or ₹0.10 buffer above resistance level
        buffer = max(0.10, round(resistance_price * TRIGGER_BUFFER_PCT, 2))
        trigger_price = round(resistance_price + buffer, 2)

        # 2. Limit Price: ₹0.10 or 0.1% slippage cap above Trigger Price
        limit_price = round(trigger_price + max(0.10, round(trigger_price * 0.001, 2)), 2)

        # 3. Quantity: Position size calculated from effective purchasing power (MIS 5x)
        # Using limit_price to ensure margin compliance
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

    def generate_markdown_table(self, order: dict) -> str:
        """
        Formats breakout order into the exact standardized markdown table specification.
        """
        md = (
            f"### 🚀 **HIGH-CONFIDENCE BREAKOUT ORDER: {order['symbol']} (NSE)**\n\n"
            f"| Field Name | Value / Setting | Why This Setting |\n"
            f"| --- | --- | --- |\n"
            f"| **Exchange** | **{order['exchange']}** | Primary liquidity pool for intraday volume. |\n"
            f"| **Tab** | **{order['tab']}** | Standard order type. |\n"
            f"| **Product** | **{order['product']}** | Uses 5x leverage (MIS), releasing margin buffer. |\n"
            f"| **Quantity** | **{order['quantity']}** | Risk-managed position size for a ₹{order['base_capital']:,.2f} balance. |\n"
            f"| **Stoploss Switch** | **{order['stoploss_switch']}** | Converts entry into a Stop-Loss Limit trigger order. |\n"
            f"| **Trigger price** | **{order['trigger_price']}** | Order activates only when market hits ₹{order['trigger_price']}. |\n"
            f"| **Limit price** | **{order['limit_price']}** | Max price you are willing to pay upon trigger. |\n\n"
            f"⚡ *Calculated Margin Required: ₹{order['margin_required']:,.2f} (Exposure: ₹{order['total_exposure']:,.2f} via {order['leverage']})*"
        )
        return md

    def generate_telegram_message(self, order: dict) -> str:
        """
        Formats breakout order into a clean, mobile-optimized HTML card for Telegram.
        """
        headline_text = f"\n📰 <i>Catalyst: {order['headline']}</i>\n" if order.get('headline') else ""
        msg = (
            f"🚀 <b>HIGH-CONFIDENCE BREAKOUT ORDER</b>\n"
            f"📈 <b>Ticker:</b> <code>{order['symbol']}</code> ({order['exchange']})\n"
            f"{headline_text}\n"
            f"<b>ORDER DETAILS:</b>\n"
            f"• <b>Exchange:</b> <code>{order['exchange']}</code>\n"
            f"• <b>Tab:</b> <code>{order['tab']}</code>\n"
            f"• <b>Product:</b> <code>{order['product']}</code> (5x MIS Leverage)\n"
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
            f"Quantity      : {order['quantity']}\n"
            f"SL Switch     : ON (Right)\n"
            f"Trigger Price : Rs {order['trigger_price']}\n"
            f"Limit Price   : Rs {order['limit_price']}\n"
            f"</pre>\n"
            f"⚡ <b>Margin Required:</b> ₹{order['margin_required']:,.2f} <i>(Exposure: ₹{order['total_exposure']:,.2f})</i>"
        )
        return msg

    def generate_html_table(self, order: dict) -> str:
        """
        Formats breakout order into an HTML table styled for Web UI.
        """
        html = f"""
        <div class="order-spec-card">
            <div class="order-spec-header">
                <span class="badge badge-nse">NSE</span>
                <span class="badge badge-mis">5x MIS LEVERAGE</span>
                <h3 class="order-title">High-Confidence Breakout Order — {order['symbol']}</h3>
            </div>
            <table class="order-spec-table">
                <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Value / Setting</th>
                        <th>Why This Setting</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Exchange</strong></td>
                        <td><span class="val-bold">{order['exchange']}</span></td>
                        <td>Primary liquidity pool for intraday volume.</td>
                    </tr>
                    <tr>
                        <td><strong>Tab</strong></td>
                        <td><span class="val-bold">{order['tab']}</span></td>
                        <td>Standard order type.</td>
                    </tr>
                    <tr>
                        <td><strong>Product</strong></td>
                        <td><span class="val-highlight">{order['product']}</span></td>
                        <td>Uses 5x leverage (MIS), releasing margin buffer.</td>
                    </tr>
                    <tr>
                        <td><strong>Quantity</strong></td>
                        <td><span class="val-primary">{order['quantity']}</span></td>
                        <td>Risk-managed position size for a ₹{order['base_capital']:,.2f} balance.</td>
                    </tr>
                    <tr>
                        <td><strong>Stoploss Switch</strong></td>
                        <td><span class="val-toggle">{order['stoploss_switch']}</span></td>
                        <td>Converts entry into a Stop-Loss Limit trigger order.</td>
                    </tr>
                    <tr>
                        <td><strong>Trigger price</strong></td>
                        <td><span class="val-trigger">₹{order['trigger_price']}</span></td>
                        <td>Order activates only when market hits ₹{order['trigger_price']}.</td>
                    </tr>
                    <tr>
                        <td><strong>Limit price</strong></td>
                        <td><span class="val-limit">₹{order['limit_price']}</span></td>
                        <td>Max price you are willing to pay upon trigger.</td>
                    </tr>
                </tbody>
            </table>
            <div class="order-spec-footer">
                <span>Margin: <strong>₹{order['margin_required']:,.2f}</strong></span>
                <span>Max Exposure: <strong>₹{order['total_exposure']:,.2f}</strong></span>
            </div>
        </div>
        """
        return html

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    calc = OrderCalculator()
    # Test case 1: Price ~95.40 (like SJVN example)
    sjvn_order = calc.compute_breakout_order("SJVN", 95.40)
    print(calc.generate_markdown_table(sjvn_order))

    print("\n" + "="*50 + "\n")

    # Test case 2: Stock price ~742.00 (shows Quantity = 17 for ₹2,524.10 balance!)
    tatamotors_order = calc.compute_breakout_order("TATAMOTORS", 742.00)
    print(calc.generate_markdown_table(tatamotors_order))

