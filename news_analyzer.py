"""
News & Catalyst Processing Engine.
Ingests 100% real-time breaking headlines from Moneycontrol, Economic Times, Livemint, and Google News RSS feeds.
Dynamically tracks and maps news events to ALL NSE listed stock tickers and scores sentiment.
"""

import re
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
import urllib.parse
from datetime import datetime
from config import SENTIMENT_THRESHOLD, NSE_COMPANIES_DATABASE

# Financial sentiment dictionary with positive and negative keyword weights
POSITIVE_FINANCIAL_WORDS = {
    "surge": 0.45, "soar": 0.50, "rally": 0.45, "jump": 0.40, "gain": 0.35, "spike": 0.40,
    "breakout": 0.60, "record high": 0.55, "profit": 0.40, "revenue growth": 0.45,
    "order win": 0.55, "contract": 0.35, "approval": 0.45, "bullish": 0.50, "upgrade": 0.45,
    "beat": 0.40, "outperform": 0.45, "expansion": 0.35, "partnership": 0.40,
    "dividend": 0.30, "robust": 0.35, "strong": 0.30, "acquisition": 0.35,
    "multibagger": 0.60, "target raised": 0.50, "buy rating": 0.50
}

NEGATIVE_FINANCIAL_WORDS = {
    "fall": -0.40, "drop": -0.40, "plunge": -0.55, "slump": -0.50, "decline": -0.35,
    "loss": -0.45, "downgrade": -0.50, "bearish": -0.45, "crash": -0.60, "penalty": -0.45,
    "investigation": -0.55, "probe": -0.50, "miss": -0.35, "weak": -0.30, "default": -0.65,
    "fraud": -0.70, "sanction": -0.50, "debt": -0.35, "slash": -0.40
}

class NewsAnalyzer:
    """
    Financial NLP engine operating exclusively on 100% live real-time market data.
    """

    def __init__(self, database=None):
        self.database = database or NSE_COMPANIES_DATABASE
        self.ticker_map = self._build_ticker_map()

    def _build_ticker_map(self):
        mapping = {}
        for item in self.database:
            symbol = item["symbol"].upper()
            name = item["name"].upper()
            mapping[symbol] = symbol
            mapping[name] = symbol

            words = name.split()
            if len(words) >= 2:
                mapping[" ".join(words[:2])] = symbol
                mapping[words[0]] = symbol
        return mapping

    def calculate_sentiment(self, text: str) -> float:
        """
        Calculates financial sentiment score (-1.0 to +1.0).
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
            score = max(-1.0, min(1.0, score / max(1, matches ** 0.5)))
        else:
            score = 0.05

        return round(score, 2)

    def extract_ticker(self, text: str) -> str:
        """
        Extracts matching NSE ticker symbol dynamically from headlines.
        """
        text_upper = text.upper()
        
        # 1. Exact alias/database match
        for alias, symbol in sorted(self.ticker_map.items(), key=lambda x: len(x[0]), reverse=True):
            if len(alias) >= 3 and re.search(r'\b' + re.escape(alias) + r'\b', text_upper):
                return symbol

        # 2. Dynamic NSE Ticker extraction pattern (uppercase 3-10 letter symbols)
        potential_tickers = re.findall(r'\b[A-Z]{3,10}\b', text_upper)
        ignored_words = {"THE", "FOR", "AND", "NEW", "BUY", "SELL", "STOCK", "STOCKS", "INDIA", "MARKET", "NIFTY", "SENSEX", "BANK", "YOY", "Q1", "Q2", "Q3", "Q4", "CRORE", "LAKH", "HIGH", "LOW", "NEWS", "GAIN", "FALL"}
        for t in potential_tickers:
            if t not in ignored_words and len(t) >= 3:
                return t

        return None

    def _fetch_rss(self, url: str, source_name: str) -> list:
        """
        Helper to parse an XML RSS feed.
        """
        headlines = []
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urlopen(req, timeout=6) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                for item in root.findall('.//item')[:15]:
                    title = item.find('title').text if item.find('title') is not None else ""
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    link = item.find('link').text if item.find('link') is not None else ""
                    
                    symbol = self.extract_ticker(title)
                    sentiment = self.calculate_sentiment(title)
                    
                    if symbol:
                        headlines.append({
                            "title": title.strip(),
                            "symbol": symbol,
                            "sentiment_score": sentiment,
                            "source": source_name,
                            "timestamp": pub_date or datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "link": link
                        })
        except Exception as e:
            print(f"[News Analyzer] Error fetching live RSS feed '{source_name}': {e}")
        return headlines

    def fetch_live_market_news(self) -> list:
        """
        Fetches 100% real-time headlines across major Indian financial news feeds.
        """
        all_headlines = []

        # Feed 1: Google News RSS for Indian Stock Market Breakouts
        google_query = urllib.parse.quote("NSE stock breakout India market")
        google_url = f"https://news.google.com/rss/search?q={google_query}&hl=en-IN&gl=IN&ceid=IN:en"
        all_headlines.extend(self._fetch_rss(google_url, "Google News RSS"))

        # Feed 2: Moneycontrol Business & Top News
        mc_url = "https://www.moneycontrol.com/rss/business.xml"
        all_headlines.extend(self._fetch_rss(mc_url, "Moneycontrol"))

        # Feed 3: Economic Times Markets Feed
        et_url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
        all_headlines.extend(self._fetch_rss(et_url, "Economic Times"))

        # Feed 4: Livemint Markets Feed
        mint_url = "https://www.livemint.com/rss/markets"
        all_headlines.extend(self._fetch_rss(mint_url, "Livemint"))

        return all_headlines

    def analyze_market_news(self) -> list:
        """
        Fetches live RSS headlines across financial portals, extracts NSE symbols,
        and filters high-conviction catalysts (Sentiment Score >= SENTIMENT_THRESHOLD).
        Exclusively relies on real-time data.
        """
        live_news = self.fetch_live_market_news()
        print(f"[News Analyzer] Ingested {len(live_news)} real-time headlines from financial feeds.")

        filtered_candidates = []
        seen_symbols = set()

        for item in live_news:
            symbol = item.get("symbol")
            score = item.get("sentiment_score", 0.0)
            
            if symbol and score >= SENTIMENT_THRESHOLD and symbol not in seen_symbols:
                filtered_candidates.append(item)
                seen_symbols.add(symbol)

        return filtered_candidates

if __name__ == "__main__":
    analyzer = NewsAnalyzer()
    candidates = analyzer.analyze_market_news()
    print(f"\nAnalyzed Live NSE Candidates (Sentiment Score >= {SENTIMENT_THRESHOLD}):")
    for c in candidates:
        print(f"[{c['symbol']}] Score: {c['sentiment_score']} | Source: {c['source']} | Headline: {c['title']}")
