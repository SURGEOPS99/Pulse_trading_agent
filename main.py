"""
Autonomous Multi-Agent NSE Pre-Market Telegram Agent.
Runs daily pre-market scan at 08:30 AM IST AND listens for mobile Telegram commands (/scan).
Orchestrates Market Data, Technical Analysis, News Intelligence, and Risk engines.
Monitors bought stocks intraday and alerts on trailing SL or intraday highs.
"""

import sys
import io
import time
from datetime import datetime
from config import BASE_CAPITAL, MIS_LEVERAGE, TELEGRAM_CHAT_ID, PRICE_CHECK_INTERVAL

from market_data import MarketDataCollector
from technical_analyzer import TechnicalAnalyzer
from news_analyzer import NewsAnalyzer
from signal_engine import SignalEngine
from order_calculator import OrderCalculator
from notifier import MobileNotifier
from price_monitor import PriceMonitor

class IntradayTelegramAgent:
    """
    Autonomous Intraday Orchestrator (Agentic Architecture).
    """

    def __init__(self, capital: float = BASE_CAPITAL, leverage: float = MIS_LEVERAGE):
        self.capital = capital
        self.leverage = leverage
        
        # Initialize Multi-Agent Pipeline
        self.market_data = MarketDataCollector()
        
        # Load complete NSE equity universe dynamically
        self.equity_list = self.market_data.fetch_nse_equity_list()
        
        self.technical_analyzer = TechnicalAnalyzer()
        self.news_analyzer = NewsAnalyzer(self.equity_list)
        self.signal_engine = SignalEngine()
        self.order_calculator = OrderCalculator(base_capital=capital, max_leverage=leverage)
        self.notifier = MobileNotifier()
        self.price_monitor = PriceMonitor(self.market_data)
        
        self.last_update_id = 0
        self.last_signals = {}  # { "SYMBOL": order_dict }

    def scan_market(self) -> list:
        """
        Executes a pre-market scan pass using the multi-agent pipeline:
        1. Agent 2 (News): Analyzes financial news & deduplicates.
        2. Agent 1 & 3 (Data/Tech): Computes SMA, RSI, ATR for candidates.
        3. Agent 4 (Signal): Synthesizes multi-factor composite scores.
        4. Agent 5 (Risk): Computes dynamic position sizing and SL.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("="*75)
        print(f" 🌅 NSE MULTI-AGENT SCANNER EXECUTION [{now_str}]")
        print("="*75)
        
        # 1. News Intelligence
        print("[Pipeline] 1/4 - Analyzing News Catalysts...")
        news_analysis = self.news_analyzer.analyze_market_news()
        
        if not news_analysis:
            print("  └─ No high-conviction catalysts found today.")
            self.notifier.send_telegram("ℹ️ <b>Market Scan Complete</b>\nNo high-conviction catalysts found right now.")
            return []
            
        print(f"  └─ Found {len(news_analysis)} stocks with news sentiment.")
        
        # 2. Technical Analysis
        print("[Pipeline] 2/4 - Computing Technical Indicators...")
        raw_signals = []
        for symbol, news_data in news_analysis.items():
            print(f"     -> Fetching data for {symbol}...")
            quote = self.market_data.fetch_stock_quote(symbol)
            history = self.market_data.fetch_stock_history(symbol, days=20)
            
            if quote and history:
                tech_data = self.technical_analyzer.analyze(symbol, history, quote)
                
                # 3. Signal Synthesis
                signal = self.signal_engine.synthesize(tech_data, news_analysis)
                raw_signals.append(signal)
            else:
                print(f"     -> [Warning] Incomplete market data for {symbol}, skipping.")

        # Filter & Rank Top Signals
        print("[Pipeline] 3/4 - Synthesizing & Ranking Signals...")
        top_signals = self.signal_engine.filter_and_rank(raw_signals, max_alerts=5)
        
        if not top_signals:
            print("  └─ No signals passed the multi-factor threshold.")
            self.notifier.send_telegram("ℹ️ <b>Market Scan Complete</b>\nNo stocks passed technical/sentiment thresholds.")
            return []

        print(f"  └─ Identified Top {len(top_signals)} Actionable Breakouts.")

        # 4. Risk & Order Generation
        print("[Pipeline] 4/4 - Computing Risk & Dispatching...")
        signals_sent = []
        
        for signal in top_signals:
            symbol = signal["symbol"]
            score = signal["composite_score"]
            
            # Agent 5 computes precise risk-scaled order
            order_dict = self.order_calculator.compute_breakout_order(signal, custom_capital=self.capital)
            
            tele_msg = self.order_calculator.generate_telegram_message(order_dict)

            print(f"\n  🎯 BREAKOUT SIGNAL: {symbol} | Composite Score: {score}")
            print(f"     Qty: {order_dict['quantity']} | Trigger: ₹{order_dict['trigger_price']} | SL: ₹{order_dict['stop_loss']}")

            # Dispatch strictly to Telegram
            self.notifier.dispatch_breakout_alert(order_dict, telegram_msg=tele_msg)
            signals_sent.append(order_dict)

            # Cache signal for /bought auto-fill
            self.last_signals[symbol] = order_dict

        print("\n" + "="*75)
        print(f" ✅ Scan Pass Completed. Delivered {len(signals_sent)} Telegram Alerts.")
        print("="*75)

        return signals_sent

    def _handle_bought_command(self, args: str):
        """Handles /bought SYMBOL [PRICE] [QTY] command."""
        parts = args.strip().split()
        if not parts:
            self.notifier.send_telegram(
                "⚠️ <b>Usage:</b> <code>/bought SYMBOL PRICE [QTY]</code>\n"
                "Example: <code>/bought TATAMOTORS 993.50</code>\n"
                "Or just: <code>/bought TATAMOTORS</code> (uses last alert price)"
            )
            return

        symbol = parts[0].upper()

        # Validate symbol exists in dynamically loaded equity list
        stock_info = next((s for s in self.equity_list if s["symbol"] == symbol), None)
        if not stock_info:
            self.notifier.send_telegram(f"❌ <b>Unknown symbol:</b> <code>{symbol}</code>. Not found in NSE database.")
            return

        buy_price = None
        quantity = 1

        if len(parts) >= 2:
            try:
                buy_price = float(parts[1])
            except ValueError:
                self.notifier.send_telegram(f"❌ <b>Invalid price:</b> <code>{parts[1]}</code>. Must be a number.")
                return

        if len(parts) >= 3:
            try:
                quantity = int(parts[2])
            except ValueError:
                quantity = 1

        if buy_price is None:
            last_signal = self.last_signals.get(symbol)
            if last_signal:
                buy_price = float(last_signal["trigger_price"])
                quantity = last_signal.get("quantity", 1) if quantity == 1 else quantity
                self.notifier.send_telegram(
                    f"📌 Auto-filled from last alert:\n"
                    f"• Price: <code>₹{buy_price:.2f}</code>\n"
                    f"• Qty: <code>{quantity}</code>"
                )
            else:
                self.notifier.send_telegram(
                    f"⚠️ No recent alert found for <code>{symbol}</code>.\n"
                    f"Please specify price: <code>/bought {symbol} PRICE</code>"
                )
                return

        self.price_monitor.add_stock(symbol, buy_price, quantity)

        confirm_msg = (
            f"✅ <b>POSITION TRACKED — {symbol}</b>\n\n"
            f"• <b>Buy Price:</b> <code>₹{buy_price:.2f}</code>\n"
            f"• <b>Quantity:</b> <code>{quantity}</code>\n"
            f"• <b>Invested:</b> <code>₹{buy_price * quantity:,.2f}</code>\n\n"
            f"🔔 Agent 6 is monitoring. You will receive <b>Trailing SL</b> or <b>Sell alerts</b>.\n"
            f"Send <code>/sold {symbol}</code> after you sell to stop monitoring."
        )
        self.notifier.send_telegram(confirm_msg)

    def _handle_sold_command(self, args: str):
        symbol = args.strip().split()[0].upper() if args.strip() else ""

        if not symbol:
            self.notifier.send_telegram(
                "⚠️ <b>Usage:</b> <code>/sold SYMBOL</code>\n"
                "Example: <code>/sold TATAMOTORS</code>"
            )
            return

        entry = self.price_monitor.watchlist.get(symbol)
        if not entry:
            self.notifier.send_telegram(f"❌ <code>{symbol}</code> is not in your watchlist.")
            return

        summary_msg = self.price_monitor.generate_sold_summary(symbol, entry)
        self.price_monitor.remove_stock(symbol)
        self.notifier.send_telegram(summary_msg)

    def _handle_watchlist_command(self):
        msg = self.price_monitor.generate_watchlist_message()
        self.notifier.send_telegram(msg)

    def check_mobile_telegram_triggers(self):
        updates = self.notifier.get_updates(offset=self.last_update_id + 1)
        for update in updates:
            self.last_update_id = max(self.last_update_id, update.get("update_id", 0))
            
            message = update.get("message", {})
            text = message.get("text", "").strip()
            sender_chat_id = str(message.get("chat", {}).get("id", ""))

            if text and sender_chat_id == str(TELEGRAM_CHAT_ID):
                print(f"\n[Telegram Mobile Command]: '{text}'")
                
                cmd_parts = text.split(maxsplit=1)
                cmd = cmd_parts[0].lower()
                cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else ""

                if cmd in ["/scan", "scan", "/trigger", "trigger", "/start", "start", "/order"]:
                    self.notifier.send_telegram("⚡ <b>Manual Multi-Agent Scan Triggered!</b>\nFetching live market data and evaluating catalysts...")
                    self.scan_market()

                elif cmd in ["/status", "status", "/help", "help"]:
                    watchlist_count = len(self.price_monitor.watchlist)
                    status_msg = (
                        f"🤖 <b>NSE MULTI-AGENT STATUS</b>\n"
                        f"• <b>Universe:</b> {len(self.equity_list)} NSE Equities\n"
                        f"• <b>Base Capital:</b> ₹{self.capital:,.2f}\n"
                        f"• <b>Max Leverage:</b> {self.leverage}x\n"
                        f"• <b>Schedule:</b> Daily 08:30 AM IST\n"
                        f"• <b>Monitoring:</b> {watchlist_count} active position(s)\n"
                        f"• <b>Market:</b> {'🟢 OPEN' if self.price_monitor.is_market_open() else '🔴 CLOSED'}\n\n"
                        f"<b>Commands:</b>\n"
                        f"• <code>/scan</code> — Trigger immediate market scan\n"
                        f"• <code>/bought SYMBOL PRICE</code> — Track a bought stock\n"
                        f"• <code>/sold SYMBOL</code> — Stop tracking a stock\n"
                        f"• <code>/watchlist</code> — View all monitored positions"
                    )
                    self.notifier.send_telegram(status_msg)

                elif cmd in ["/bought", "bought"]:
                    self._handle_bought_command(cmd_args)

                elif cmd in ["/sold", "sold"]:
                    self._handle_sold_command(cmd_args)

                elif cmd in ["/watchlist", "watchlist", "/positions", "positions"]:
                    self._handle_watchlist_command()

    def _run_price_monitor_cycle(self):
        if not self.price_monitor.watchlist:
            return

        if self.price_monitor.is_market_open():
            alerts = self.price_monitor.check_intraday_highs_and_sl()
            for alert in alerts:
                msg = self.price_monitor.generate_sell_alert_message(alert)
                self.notifier.dispatch_sell_alert(alert["symbol"], msg)

        if self.price_monitor.should_send_eod_summary():
            eod_msg = self.price_monitor.generate_eod_summary()
            if eod_msg:
                self.notifier.send_telegram(eod_msg)
                self.price_monitor.mark_eod_sent()
                print("[Agent] End-of-day P&L summary dispatched to Telegram.")

    def run_daily_and_mobile_listener(self, target_time_str: str = "08:30"):
        print("="*75)
        print("   NSE MULTI-AGENT ORCHESTRATOR (DAILY 08:30 AM + PHONE TRIGGER)")
        print("="*75)
        print(f" Account Capital : ₹{self.capital:,.2f}")
        print(f" Max Leverage    : {self.leverage}x")
        print(f" Monitored Stocks: {len(self.equity_list)}")
        print(f" Scheduled Run   : Daily at {target_time_str} AM IST")
        print(f" Phone Trigger   : Send '/scan' on Telegram from your phone anytime!")
        print("="*75)

        start_msg = (
            f"🚀 <b>NSE Multi-Agent Pipeline Active!</b>\n"
            f"• <b>Universe:</b> {len(self.equity_list)} stocks loaded\n"
            f"• <b>Daily Schedule:</b> 08:30 AM IST\n"
            f"• <b>Phone Trigger:</b> Send <code>/scan</code> anytime\n"
        )
        self.notifier.send_telegram(start_msg)

        last_daily_run_date = None
        last_price_check = 0

        while True:
            self.check_mobile_telegram_triggers()

            now = datetime.now()
            target_hour, target_minute = map(int, target_time_str.split(":"))
            today_date_str = now.strftime("%Y-%m-%d")

            if now.hour == target_hour and now.minute == target_minute and last_daily_run_date != today_date_str:
                print(f"\n[Daily Schedule Triggered]: Executing 08:30 AM Morning Scan...")
                self.notifier.send_telegram("🌅 <b>Executing Scheduled 08:30 AM Multi-Agent Scan...</b>")
                self.scan_market()
                last_daily_run_date = today_date_str

            current_time = time.time()
            if (current_time - last_price_check) >= PRICE_CHECK_INTERVAL:
                self._run_price_monitor_cycle()
                last_price_check = current_time

            time.sleep(3)

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    agent = IntradayTelegramAgent()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        agent.scan_market()
    else:
        agent.run_daily_and_mobile_listener(target_time_str="08:30")
