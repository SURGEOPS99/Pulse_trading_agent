"""
News Intelligence (Agent 2)
Ingests live headlines, deduplicates, and calculates sentiment with TF-IDF concepts and source weighting.
Dynamic NSE equity list mapping.
"""

import re
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
import urllib.parse
from datetime import datetime, timedelta
import collections

# Financial sentiment dictionary with positive and negative keyword weights (proxy for TF-IDF importance)
# Higher weights represent rarer, more impactful financial terms
POSITIVE_FINANCIAL_WORDS = {
    "surge": 0.45, "soar": 0.50, "rally": 0.45, "jump": 0.40, "gain": 0.35, "spike": 0.40,
    "record high": 0.55, "profit": 0.45, "revenue growth": 0.50,
    "order win": 0.60, "contract": 0.45, "approval": 0.50, "bullish": 0.50, "upgrade": 0.50,
    "beat": 0.40, "outperform": 0.45, "expansion": 0.40, "partnership": 0.40,
    "dividend": 0.30, "robust": 0.35, "strong": 0.30, "acquisition": 0.40,
    "target raised": 0.55, "buy rating": 0.50, "mandate": 0.50, "secured": 0.45,
    "breakout": 0.35 # Now it's a sentiment word, not a ticker
}

NEGATIVE_FINANCIAL_WORDS = {
    "fall": -0.40, "drop": -0.40, "plunge": -0.55, "slump": -0.50, "decline": -0.35,
    "loss": -0.45, "downgrade": -0.50, "bearish": -0.45, "crash": -0.60, "penalty": -0.45,
    "investigation": -0.55, "probe": -0.50, "miss": -0.35, "weak": -0.30, "default": -0.65,
    "fraud": -0.70, "sanction": -0.50, "debt": -0.35, "slash": -0.40
}

# Words that indicate generic clickbait or non-actionable listicles
NOISE_PATTERNS = [
    r'\bpenny\b', r'\bpenny stocks\b', r'\bdo you own\b', r'\bhow the legendary\b',
    r'\b5 shares to buy\b', r'\b10 stocks\b', r'\bpenny stocks surged\b',
    r'\bchartist talk\b', r'\bview on\b', r'\bwhat should investors do\b',
    r'\bbreakout stocks to buy\b', r'\bshares to buy today\b', r'\brecommends five shares\b'
]

# Non-stock English trading terms that must NEVER be extracted as stock symbols
NON_STOCK_WORDS = {
    "BREAKOUT", "PENNY", "CHARTIST", "BILL", "BUY", "SELL", "STOCK", "STOCKS",
    "INDIA", "MARKET", "NIFTY", "SENSEX", "BANK", "YOY", "Q1", "Q2", "Q3", "Q4",
    "CRORE", "LAKH", "HIGH", "LOW", "NEWS", "GAIN", "FALL", "SHARE", "SHARES",
    "TODAY", "WEEK", "MONTH", "YEAR", "REPORT", "REPORTS", "TARGET", "EXPERT",
    "LIMITED", "LTD", "CORP", "CORPORATION", "INC", "HOLDINGS"
}

SOURCE_WEIGHTS = {
    "Moneycontrol": 1.2,
    "Economic Times": 1.1,
    "Livemint": 1.0,
    "Google News": 0.9,
    "default": 1.0
}

class NewsAnalyzer:
    """
    Expert stock market analyst engine enforcing strict NSE listed company validation.
    """

    def __init__(self, equity_list: list):
        self.equity_list = equity_list
        self.valid_tickers = {item["symbol"].upper(): item for item in self.equity_list}
        self.ticker_alias_map = self._build_ticker_alias_map()

    def _build_ticker_alias_map(self):
        mapping = {}
        for item in self.equity_list:
            symbol = item["symbol"].upper()
            name = item["name"].upper()
            mapping[symbol] = symbol
            
            clean_name = re.sub(r'\b(LIMITED|LTD|CORPORATION|CORP|INDUSTRIES|IND|COMPANY|CO)\b', '', name).strip()
            if len(clean_name) >= 3 and clean_name not in NON_STOCK_WORDS:
                mapping[clean_name] = symbol
            
            words = clean_name.split()
            if len(words) >= 2:
                two_words = " ".join(words[:2])
                if two_words not in NON_STOCK_WORDS:
                    mapping[two_words] = symbol
            if len(words) >= 1 and len(words[0]) >= 4 and words[0] not in {"STATE", "POWER", "BHARAT", "INDIAN", "FIRST", "BANK", "BAJAJ", "TATA", "ADANI"}:
                mapping[words[0]] = symbol
        return mapping

    def calculate_sentiment(self, text: str, source: str = "default") -> float:
        """
        Calculates financial sentiment score (-1.0 to +1.0) with source weighting.
        """
        text_lower = text.lower()
        score = 0.0
        matches = 0

        for word, weight in POSITIVE_FINANCIAL_WORDS.items():
            if word in text_lower:
                score += weight
                matches += 1

        for word, weight in NEGATIVE_FINANCIAL_WORDS.items():
            if word in text_lower:
                score += weight
                matches += 1

        if matches > 0:
            raw_score = score / max(1, matches ** 0.5)
            # Apply source weight
            source_weight = SOURCE_WEIGHTS.get(source, SOURCE_WEIGHTS["default"])
            final_score = max(-1.0, min(1.0, raw_score * source_weight))
        else:
            final_score = 0.05

        return round(final_score, 2)

    def extract_validated_nse_ticker(self, text: str) -> str:
        """
        Extracts ONLY officially listed, validated NSE stock tickers.
        """
        text_upper = text.upper()

        # Check noise pattern filter first
        for pat in NOISE_PATTERNS:
            if re.search(pat, text.lower()):
                return None

        # Search for exact ticker or alias match
        for alias, symbol in sorted(self.ticker_alias_map.items(), key=lambda x: len(x[0]), reverse=True):
            if symbol not in NON_STOCK_WORDS and len(alias) >= 3 and re.search(r'\b' + re.escape(alias) + r'\b', text_upper):
                return symbol

        return None

    def _fetch_rss(self, url: str, source_name: str) -> list:
        headlines = []
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urlopen(req, timeout=6) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                for item in root.findall('.//item')[:30]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    
                    symbol = self.extract_validated_nse_ticker(title)
                    sentiment = self.calculate_sentiment(title, source_name)
                    
                    if symbol and symbol in self.valid_tickers and symbol not in NON_STOCK_WORDS:
                        headlines.append({
                            "title": title.strip(),
                            "symbol": symbol,
                            "sentiment_score": sentiment,
                            "source": source_name,
                            "timestamp": pub_date or datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "link": link
                        })
        except Exception as e:
            print(f"[News Analyzer] Live RSS feed '{source_name}' error: {e}")
        return headlines

    def fetch_live_market_news(self) -> list:
        """Fetches headlines from all sources."""
        all_headlines = []

        # Google News RSS
        google_query = urllib.parse.quote("NSE stock order earnings sales India")
        google_url = f"https://news.google.com/rss/search?q={google_query}&hl=en-IN&gl=IN&ceid=IN:en"
        all_headlines.extend(self._fetch_rss(google_url, "Google News"))

        # Moneycontrol
        mc_url = "https://www.moneycontrol.com/rss/MCtopnews.xml"
        all_headlines.extend(self._fetch_rss(mc_url, "Moneycontrol"))

        # Economic Times
        et_url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
        all_headlines.extend(self._fetch_rss(et_url, "Economic Times"))

        # Livemint
        mint_url = "https://www.livemint.com/rss/markets"
        all_headlines.extend(self._fetch_rss(mint_url, "Livemint"))

        return all_headlines

    def analyze_market_news(self) -> dict:
        """
        Scans live headlines, deduplicates, and computes aggregate sentiment per stock.
        Returns: { "SYMBOL": {"aggregated_score": float, "headlines": [...] } }
        """
        live_news = self.fetch_live_market_news()
        print(f"[News Analyzer] Ingested {len(live_news)} verified stock news headlines.")

        # Group by symbol
        grouped = collections.defaultdict(list)
        for item in live_news:
            grouped[item["symbol"]].append(item)

        results = {}
        for symbol, items in grouped.items():
            # Deduplicate similar headlines for the same stock
            unique_titles = set()
            unique_items = []
            
            for item in items:
                # Simple deduplication: take first 30 chars
                title_sig = item["title"].lower()[:30] 
                if title_sig not in unique_titles:
                    unique_titles.add(title_sig)
                    unique_items.append(item)
                    
            if not unique_items:
                continue
                
            # Aggregate score: Compounding confidence for multiple unique positive mentions
            total_score = sum(item["sentiment_score"] for item in unique_items)
            
            # Non-linear scaling: 2 positive articles > 1 positive article
            # But cap at 1.0
            aggregated_score = max(-1.0, min(1.0, total_score))
            
            # Sort headlines by score descending
            unique_items.sort(key=lambda x: x["sentiment_score"], reverse=True)
            
            results[symbol] = {
                "symbol": symbol,
                "aggregated_score": round(aggregated_score, 2),
                "headlines": unique_items
            }

        return results

if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Mock equity list for test
    equity_list = [
        {"symbol": "RELIANCE", "name": "Reliance Industries Ltd"},
        {"symbol": "TCS", "name": "Tata Consultancy Services"}
    ]
    
    analyzer = NewsAnalyzer(equity_list)
    results = analyzer.analyze_market_news()
    
    print("\n🎯 Aggregated News Signals:")
    for sym, data in results.items():
        print(f"[{sym}] Aggregate Score: {data['aggregated_score']}")
        for hl in data['headlines']:
            print(f"  - ({hl['sentiment_score']}) {hl['title']} [{hl['source']}]")
