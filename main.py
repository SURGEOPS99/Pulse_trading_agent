"""
Autonomous NSE Pre-Market Intraday Telegram Agent with Mobile Phone Triggers.
Runs daily pre-market scan at 08:30 AM IST AND listens for mobile Telegram commands (/scan).
"""

import sys
import io
import time
from datetime import datetime, timedelta
from config import BASE_CAPITAL, MIS_LEVERAGE, SENTIMENT_THRESHOLD, NSE_COMPANIES_DATABASE, TELEGRAM_CHAT_ID
from news_analyzer import NewsAnalyzer
from order_calculator import OrderCalculator
from notifier import MobileNotifier

# UTF-8 Encoding Fix for Windows Terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class IntradayTelegramAgent:
    """
    Autonomous Intraday Agent running daily at 08:30 AM IST and responding
    to instant mobile phone Telegram command triggers (/scan).
    """

    def __init__(self, capital: float = BASE_CAPITAL, leverage: float = MIS_LEVERAGE):
        self.capital = capital
        self.leverage = leverage
        self.news_analyzer = NewsAnalyzer()
        self.order_calculator = OrderCalculator(base_capital=capital, leverage=leverage)
        self.notifier = MobileNotifier()
        self.database = list(NSE_COMPANIES_DATABASE)
        self.last_update_id = 0

    def scan_market(self) -> list:
        """
        Executes a pre-market scan pass across all NSE stocks:
        1. Analyzes financial news catalysts.
        2. Filters high-conviction stocks (Sentiment > 0.40).
        3. Computes 5x MIS breakout order specs.
        4. Dispatches HTML cards directly to Telegram.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("="*65)
        print(f" 🌅 NSE PRE-MARKET SCANNER EXECUTION [{now_str}]")
        print("="*65)
        
        catalysts = self.news_analyzer.analyze_market_news()
        print(f"  └─ Identified {len(catalysts)} high-conviction catalysts (Sentiment > {SENTIMENT_THRESHOLD})")

        signals_sent = []

        for item in catalysts:
            symbol = item["symbol"]
            score = item["sentiment_score"]
            headline = item["title"]

            # Dynamic lookup across all ~2,000+ NSE companies
            stock_info = next((s for s in self.database if s["symbol"] == symbol), None)
            resistance = stock_info["resistance"] if stock_info else 250.00

            order_dict = self.order_calculator.compute_breakout_order(symbol, resistance, custom_capital=self.capital)
            order_dict["sentiment_score"] = score
            order_dict["headline"] = headline

            tele_msg = self.order_calculator.generate_telegram_message(order_dict)

            print(f"\n  🎯 BREAKOUT SIGNAL: {symbol} | Sentiment: {score}")
            print(f"     Qty: {order_dict['quantity']} | Trigger: ₹{order_dict['trigger_price']} | Limit: ₹{order_dict['limit_price']}")

            # Dispatch strictly to Telegram
            self.notifier.dispatch_breakout_alert(order_dict, telegram_msg=tele_msg)
            signals_sent.append(order_dict)

        print("\n" + "="*65)
        print(f" ✅ Scan Pass Completed. Delivered {len(signals_sent)} Telegram Alerts.")
        print("="*65)

        return signals_sent

    def check_mobile_telegram_triggers(self):
        """
        Listens for incoming command messages sent by the user on Telegram (/scan, /status, /start).
        """
        updates = self.notifier.get_updates(offset=self.last_update_id + 1)
        for update in updates:
            self.last_update_id = max(self.last_update_id, update.get("update_id", 0))
            
            message = update.get("message", {})
            text = message.get("text", "").strip()
            sender_chat_id = str(message.get("chat", {}).get("id", ""))

            # Verify sender chat ID for security
            if text and sender_chat_id == str(TELEGRAM_CHAT_ID):
                print(f"\n[Telegram Mobile Command Received]: '{text}' from Chat ID {sender_chat_id}")
                
                cmd = text.lower()
                if cmd in ["/scan", "scan", "/trigger", "trigger", "/start", "start", "/order"]:
                    self.notifier.send_telegram("⚡ <b>Manual Pre-Market Scan Triggered from Phone!</b>\nScanning news catalysts across all NSE companies...")
                    self.scan_market()
                elif cmd in ["/status", "status", "/help", "help"]:
                    status_msg = (
                        f"🤖 <b>NSE INTRADAY AGENT STATUS</b>\n"
                        f"• <b>Base Capital:</b> ₹{self.capital:,.2f}\n"
                        f"• <b>Leverage:</b> {self.leverage}x MIS (Effective: ₹{self.capital * self.leverage:,.2f})\n"
                        f"• <b>Schedule:</b> Daily 08:30 AM IST\n"
                        f"• <b>Mobile Commands:</b> Type <code>/scan</code> anytime on phone to trigger immediate scan!"
                    )
                    self.notifier.send_telegram(status_msg)

    def run_daily_and_mobile_listener(self, target_time_str: str = "08:30"):
        """
        Dual Mode Loop:
        1. Listens continuously for phone Telegram commands (/scan).
        2. Executes daily scheduled scan at 08:30 AM IST.
        """
        print("="*65)
        print("   NSE PRE-MARKET TELEGRAM AGENT (DAILY 08:30 AM + PHONE TRIGGER)")
        print("="*65)
        print(f" Account Capital : ₹{self.capital:,.2f}")
        print(f" MIS Leverage   : {self.leverage}x MIS (Purchasing Power: ₹{self.capital * self.leverage:,.2f})")
        print(f" Scheduled Run   : Daily at {target_time_str} AM IST")
        print(f" Phone Trigger   : Send '/scan' on Telegram from your phone anytime!")
        print("="*65)

        # Notify user on Telegram that bot is listening for phone commands
        start_msg = (
            f"🚀 <b>NSE Intraday Agent Active & Listening!</b>\n"
            f"• <b>Daily Schedule:</b> 08:30 AM IST\n"
            f"• <b>Phone Trigger:</b> Send <code>/scan</code> anytime from your phone to trigger a manual scan!"
        )
        self.notifier.send_telegram(start_msg)

        last_daily_run_date = None

        while True:
            # 1. Check for incoming mobile commands from Telegram
            self.check_mobile_telegram_triggers()

            # 2. Check daily 08:30 AM schedule
            now = datetime.now()
            target_hour, target_minute = map(int, target_time_str.split(":"))
            today_date_str = now.strftime("%Y-%m-%d")

            if now.hour == target_hour and now.minute == target_minute and last_daily_run_date != today_date_str:
                print(f"\n[Daily Schedule Triggered]: Executing 08:30 AM Morning Scan...")
                self.notifier.send_telegram("🌅 <b>Executing Scheduled 08:30 AM Morning Pre-Market Scan...</b>")
                self.scan_market()
                last_daily_run_date = today_date_str

            time.sleep(3)

if __name__ == "__main__":
    agent = IntradayTelegramAgent()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        agent.scan_market()
    else:
        agent.run_daily_and_mobile_listener(target_time_str="08:30")
