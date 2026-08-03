"""
Telegram Real-Time Intraday Alert Dispatcher & Interactive Command Listener.
Dispatches formatted HTML breakout order cards and listens for mobile Telegram triggers (/scan, /status).
"""

import json
import urllib.request
import urllib.parse
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class MobileNotifier:
    """
    Handles Telegram Bot API alerts and interactive mobile commands.
    """

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID

    def send_telegram(self, message: str, parse_mode: str = "HTML") -> dict:
        """
        Sends HTML formatted alert card to Telegram chat via Bot API.
        """
        if not self.bot_token or not self.chat_id:
            print("[Telegram Notifier] Telegram Bot Token or Chat ID not configured.")
            return {"status": "skipped", "reason": "Missing credentials"}

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                print(f"[Telegram Notifier] Telegram alert delivered successfully: {res_data.get('ok')}")
                return {"status": "success", "response": res_data}
        except Exception as e:
            print(f"[Telegram Notifier] Error delivering Telegram alert: {e}")
            return {"status": "error", "error": str(e)}

    def get_updates(self, offset: int = 0) -> list:
        """
        Fetches incoming messages/commands sent by the user to the Telegram bot.
        """
        if not self.bot_token:
            return []

        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates?offset={offset}&timeout=5"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if res_data.get("ok"):
                    return res_data.get("result", [])
        except Exception:
            pass
        return []

    def dispatch_breakout_alert(self, order_dict: dict, telegram_msg: str = None) -> dict:
        """
        Dispatches breakout alert strictly to Telegram.
        """
        if not telegram_msg:
            from order_calculator import OrderCalculator
            calc = OrderCalculator()
            telegram_msg = calc.generate_telegram_message(order_dict)

        print(f"\n[Telegram Dispatcher] Sending Alert for NSE Stock: {order_dict['symbol']}...")
        telegram_res = self.send_telegram(telegram_msg, parse_mode="HTML")

        return {
            "symbol": order_dict["symbol"],
            "telegram": telegram_res
        }

    def dispatch_sell_alert(self, symbol: str, message: str) -> dict:
        """
        Dispatches a sell-now intraday high alert to Telegram.
        """
        print(f"\n[Telegram Dispatcher] Sending SELL Alert for NSE Stock: {symbol}...")
        telegram_res = self.send_telegram(message, parse_mode="HTML")

        return {
            "symbol": symbol,
            "telegram": telegram_res
        }

if __name__ == "__main__":
    notifier = MobileNotifier()
    from order_calculator import OrderCalculator
    calc = OrderCalculator()
    order = calc.compute_breakout_order("TATAMOTORS", 992.00)
    order["headline"] = "Tata Motors EV sales jump 28% YoY; stock tests technical breakout"
    msg = calc.generate_telegram_message(order)
    notifier.send_telegram(msg)
