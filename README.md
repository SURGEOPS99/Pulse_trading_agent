# Autonomous NSE Real-Time Intraday Monitor & Telegram Alert Agent

An AI framework that analyzes financial news across all NSE companies, evaluates catalyst sentiment, detects technical breakout triggers, computes risk-managed intraday position sizes (5x MIS leverage for ₹2,524.10 capital balance), and dispatches formatted HTML order cards directly to Telegram.

---

## 📱 Standardized High-Confidence Breakout Order Format

Alerts delivered directly to Telegram follow this mobile card schema:

```
🚀 HIGH-CONFIDENCE BREAKOUT ORDER
📈 Ticker: TATAMOTORS (NSE)
📰 Catalyst: Tata Motors EV sales jump 28% YoY

ORDER DETAILS:
• Exchange: NSE
• Tab: Regular
• Product: Intraday (5x MIS Leverage)
• Quantity: 12 (Position size for ₹2,524.10 balance)
• Stoploss Switch: ON (Toggled Right)
• Trigger Price: ₹992.99 (Activates order)
• Limit Price: ₹993.98 (Max execution price)

📋 EXECUTION CARD:
Field           Value
-------------------------------
Exchange      : NSE
Tab           : Regular
Product       : Intraday (MIS)
Quantity      : 12
SL Switch     : ON (Right)
Trigger Price : Rs 992.99
Limit Price   : Rs 993.98

⚡ Margin Required: ₹2,524.10 (Exposure: ₹11,895.68)
```

---

## ⚡ Features & Execution Options

### 1. **Automated Daily Cloud Schedule (GitHub Actions)**
- File: `.github/workflows/daily_nse_alerts.yml`
- Runs automatically in the cloud **every morning at 08:30 AM IST** (03:00 UTC).
- **No PC/laptop required!** Telegram alerts arrive on your phone even when your laptop is turned off.

### 2. **Mobile Telegram Phone Triggers**
- Open Telegram on your phone and send:
  - `/scan` — Triggers an immediate pre-market scan pass and returns breakout orders.
  - `/status` — Displays account capital & agent health.

### 3. **Manual Local Run**
- Run pre-market scanner pass immediately:
  ```bash
  python main.py --now
  ```

---

## 🚀 How to Enable 24/7 Cloud Execution on GitHub

1. **Initialize Git & Push to your GitHub Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit of NSE Intraday Telegram Agent"
   git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
   git push -u origin main
   ```

2. **Configure GitHub Repository Secrets (Optional - Already embedded in fallback):**
   - Go to your GitHub Repo -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
   - `TELEGRAM_BOT_TOKEN`: `8815412040:AAH4iB1rFPWnmpEnQFkvQ2aUMq6hNtxqGxA`
   - `TELEGRAM_CHAT_ID`: `8313018138`

3. **Manual Cloud Trigger on GitHub:**
   - Go to **Actions** tab -> Select **"Daily NSE Intraday Telegram Pre-Market Alerts"** -> Click **"Run workflow"**.
