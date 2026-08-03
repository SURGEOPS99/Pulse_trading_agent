"""
Intraday Price Monitor & Sell Alert Engine (Agent 6).
Monitors live prices of stocks the user has bought.
Detects new intraday highs and Trailing Stop-Loss hits.
Dispatches SELL NOW alerts to Telegram.
Generates end-of-day P&L summaries.
"""

import time
from datetime import datetime

from config import (
    HIGH_ALERT_COOLDOWN,
    HIGH_ALERT_MIN_JUMP_PCT,
    MARKET_OPEN_TIME,
    MARKET_CLOSE_TIME,
    TRAILING_SL_PCT
)
from market_data import MarketDataCollector

class PriceMonitor:
    """
    Tracks bought stocks, polls market data for live prices,
    detects intraday highs and trailing SL drops, and generates alerts.
    """

    def __init__(self, market_data_collector: MarketDataCollector = None):
        self.market_data = market_data_collector or MarketDataCollector()
        self.watchlist = {}
        self._sent_eod_today = None

    # ── Watchlist Management ──────────────────────────────────────────

    def add_stock(self, symbol: str, buy_price: float, quantity: int = 1) -> dict:
        symbol = symbol.upper()
        entry = {
            "buy_price": buy_price,
            "quantity": quantity,
            "intraday_high": buy_price,
            "last_alert_price": 0.0,
            "last_alert_time": 0.0,
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.watchlist[symbol] = entry
        print(f"[Price Monitor] Added {symbol} to watchlist @ ₹{buy_price:.2f} x {quantity} qty")
        return entry

    def remove_stock(self, symbol: str) -> dict:
        symbol = symbol.upper()
        entry = self.watchlist.pop(symbol, None)
        if entry:
            print(f"[Price Monitor] Removed {symbol} from watchlist.")
        return entry

    # ── Intraday Detection ───────────────────────────────────────

    def check_intraday_highs_and_sl(self) -> list:
        """
        Iterates over the watchlist, fetches live prices, and detects
        new intraday highs or trailing stop-loss hits.
        Returns a list of alert dicts.
        """
        if not self.watchlist:
            return []

        alerts = []
        now = time.time()

        for symbol, entry in list(self.watchlist.items()):
            price_data = self.market_data.fetch_stock_quote(symbol)
            if not price_data or price_data["price"] <= 0:
                continue

            current_price = price_data["price"]
            day_high = price_data["day_high"]
            prev_close = price_data["prev_close"]

            tracked_high = entry["intraday_high"]
            new_high = max(tracked_high, current_price, day_high)

            if new_high > tracked_high:
                entry["intraday_high"] = new_high

            buy_price = entry["buy_price"]
            quantity = entry["quantity"]
            profit_pct = ((current_price - buy_price) / buy_price) * 100
            profit_amount = (current_price - buy_price) * quantity

            # Check Trailing Stop Loss
            # Trailing SL = max_price * (1 - trailing_sl_pct)
            trailing_sl_price = new_high * (1 - TRAILING_SL_PCT)
            is_sl_hit = current_price <= trailing_sl_price and new_high > buy_price

            alert = None

            if is_sl_hit:
                alert = {
                    "symbol": symbol,
                    "type": "TRAILING_SL",
                    "current_price": current_price,
                    "buy_price": buy_price,
                    "quantity": quantity,
                    "intraday_high": new_high,
                    "profit_pct": profit_pct,
                    "profit_amount": profit_amount,
                    "reason": f"Dropped {TRAILING_SL_PCT*100}% below intraday high"
                }
                # Remove from watchlist after SL hit to prevent spam
                self.remove_stock(symbol)
            else:
                # ── Cooldown checks for High Alerts ──
                last_alert_price = entry["last_alert_price"]
                last_alert_time = entry["last_alert_time"]

                if (now - last_alert_time) >= HIGH_ALERT_COOLDOWN:
                    jump_pct = 1.0
                    if last_alert_price > 0:
                        jump_pct = (current_price - last_alert_price) / last_alert_price

                    if jump_pct >= HIGH_ALERT_MIN_JUMP_PCT and current_price >= new_high and current_price > buy_price:
                        alert = {
                            "symbol": symbol,
                            "type": "NEW_HIGH",
                            "current_price": current_price,
                            "buy_price": buy_price,
                            "quantity": quantity,
                            "intraday_high": new_high,
                            "profit_pct": profit_pct,
                            "profit_amount": profit_amount,
                            "reason": "New Intraday High"
                        }
                        entry["last_alert_price"] = current_price
                        entry["last_alert_time"] = now

            if alert:
                alerts.append(alert)
                print(f"[Price Monitor] 🔔 {alert['type']}: {symbol} ₹{current_price:.2f} ({profit_pct:+.2f}%)")

        return alerts

    # ── Telegram Message Formatting ───────────────────────────────────

    def generate_sell_alert_message(self, alert: dict) -> str:
        symbol = alert["symbol"]
        price = alert["current_price"]
        buy = alert["buy_price"]
        qty = alert["quantity"]
        pct = alert["profit_pct"]
        profit = alert["profit_amount"]
        high = alert["intraday_high"]

        if alert["type"] == "TRAILING_SL":
            title = "⚠️ <b>TRAILING STOP-LOSS HIT — SELL NOW!</b>"
            action = f"Price dropped below trailing SL. Lock in <code>₹{profit:+,.2f}</code> profit."
        else:
            title = "🔔 <b>INTRADAY HIGH — SELL ALERT</b>"
            action = f"Consider selling to lock in <code>₹{profit:+,.2f}</code> profit!"

        msg = (
            f"{title}\n"
            f"📈 <b>Ticker:</b> <code>{symbol}</code> (NSE)\n\n"
            f"<b>💰 LIVE PRICE:</b> <code>₹{price:.2f}</code> "
            f"<b>({pct:+.2f}%)</b>\n"
            f"<b>🎯 Intraday High:</b> <code>₹{high:.2f}</code>\n\n"
            f"<b>YOUR POSITION:</b>\n"
            f"• <b>Buy Price:</b> <code>₹{buy:.2f}</code>\n"
            f"• <b>Quantity:</b> <code>{qty}</code>\n"
            f"• <b>Current P&L:</b> <code>₹{profit:+,.2f}</code>\n\n"
            f"⚡ <b>Action:</b> {action}"
        )
        return msg

    def generate_watchlist_message(self) -> str:
        if not self.watchlist:
            return "📋 <b>Watchlist is empty.</b>\nBuy a stock and send <code>/bought SYMBOL PRICE</code> to start monitoring."

        lines = ["📋 <b>LIVE INTRADAY WATCHLIST</b>\n"]

        for symbol, entry in self.watchlist.items():
            price_data = self.market_data.fetch_stock_quote(symbol)
            current = price_data["price"] if price_data else 0.0
            buy = entry["buy_price"]
            qty = entry["quantity"]

            if current > 0 and buy > 0:
                pnl = (current - buy) * qty
                pnl_pct = ((current - buy) / buy) * 100
                emoji = "🟢" if pnl >= 0 else "🔴"
                lines.append(
                    f"{emoji} <b>{symbol}</b>\n"
                    f"   Buy: <code>₹{buy:.2f}</code> → Now: <code>₹{current:.2f}</code>\n"
                    f"   Qty: <code>{qty}</code> | P&L: <code>₹{pnl:+,.2f}</code> (<code>{pnl_pct:+.2f}%</code>)\n"
                )
            else:
                lines.append(
                    f"⏳ <b>{symbol}</b> — Buy: <code>₹{buy:.2f}</code> x {qty} (fetching price...)\n"
                )

        return "\n".join(lines)

    def generate_eod_summary(self) -> str:
        if not self.watchlist:
            return None

        lines = [
            f"🏁 <b>END-OF-DAY P&L SUMMARY</b>\n"
            f"📅 {datetime.now().strftime('%d %b %Y')}\n"
        ]

        total_pnl = 0.0
        total_invested = 0.0

        for symbol, entry in self.watchlist.items():
            price_data = self.market_data.fetch_stock_quote(symbol)
            current = price_data["price"] if price_data else entry["intraday_high"]
            buy = entry["buy_price"]
            qty = entry["quantity"]
            high = entry["intraday_high"]

            pnl = (current - buy) * qty
            pnl_pct = ((current - buy) / buy) * 100 if buy > 0 else 0.0
            invested = buy * qty
            total_pnl += pnl
            total_invested += invested

            emoji = "🟢" if pnl >= 0 else "🔴"
            lines.append(
                f"{emoji} <b>{symbol}</b>\n"
                f"   Buy: <code>₹{buy:.2f}</code> | Close: <code>₹{current:.2f}</code> | High: <code>₹{high:.2f}</code>\n"
                f"   Qty: <code>{qty}</code> | P&L: <code>₹{pnl:+,.2f}</code> (<code>{pnl_pct:+.2f}%</code>)\n"
            )

        total_pct = ((total_pnl / total_invested) * 100) if total_invested > 0 else 0.0
        overall_emoji = "🟢" if total_pnl >= 0 else "🔴"

        lines.append(
            f"\n{'='*30}\n"
            f"{overall_emoji} <b>TOTAL P&L:</b> <code>₹{total_pnl:+,.2f}</code> "
            f"(<code>{total_pct:+.2f}%</code>)\n"
            f"💼 <b>Capital Deployed:</b> <code>₹{total_invested:,.2f}</code>"
        )

        return "\n".join(lines)

    def generate_sold_summary(self, symbol: str, entry: dict) -> str:
        price_data = self.market_data.fetch_stock_quote(symbol)
        current = price_data["price"] if price_data else entry["intraday_high"]
        buy = entry["buy_price"]
        qty = entry["quantity"]
        high = entry["intraday_high"]

        pnl = (current - buy) * qty
        pnl_pct = ((current - buy) / buy) * 100 if buy > 0 else 0.0
        emoji = "🟢" if pnl >= 0 else "🔴"

        msg = (
            f"✅ <b>POSITION CLOSED — {symbol}</b>\n\n"
            f"• <b>Buy Price:</b> <code>₹{buy:.2f}</code>\n"
            f"• <b>Last Price:</b> <code>₹{current:.2f}</code>\n"
            f"• <b>Intraday High:</b> <code>₹{high:.2f}</code>\n"
            f"• <b>Quantity:</b> <code>{qty}</code>\n"
            f"• {emoji} <b>P&L:</b> <code>₹{pnl:+,.2f}</code> (<code>{pnl_pct:+.2f}%</code>)\n\n"
            f"Stock removed from monitoring watchlist."
        )
        return msg

    # ── Market Hours Check ────────────────────────────────────────────

    def is_market_open(self) -> bool:
        now = datetime.now()
        if now.weekday() >= 5:
            return False

        open_h, open_m = map(int, MARKET_OPEN_TIME.split(":"))
        close_h, close_m = map(int, MARKET_CLOSE_TIME.split(":"))

        market_open = now.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
        market_close = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)

        return market_open <= now <= market_close

    def should_send_eod_summary(self) -> bool:
        now = datetime.now()
        if now.weekday() >= 5:
            return False

        close_h, close_m = map(int, MARKET_CLOSE_TIME.split(":"))
        market_close = now.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
        today_str = now.strftime("%Y-%m-%d")

        if now > market_close and (now.hour == close_h and now.minute <= close_m + 10):
            if self._sent_eod_today != today_str:
                return True
        return False

    def mark_eod_sent(self):
        self._sent_eod_today = datetime.now().strftime("%Y-%m-%d")

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    pm = PriceMonitor()
    # Add a mock entry
    pm.add_stock("RELIANCE", 1250.00, 10)
    
    # Simulate SL hit
    # Force the intraday_high higher so current price (which is ~1300) will be a drop
    # Just to test formatting
    pm.watchlist["RELIANCE"]["intraday_high"] = 1500.00
    alerts = pm.check_intraday_highs_and_sl()
    
    for a in alerts:
        print(pm.generate_sell_alert_message(a))
