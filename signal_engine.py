"""
Signal Synthesizer (Agent 4)
Multi-factor scoring combining Technical Analysis, News Sentiment, and Volume.
Ranks and filters top signals.
"""

from config import SENTIMENT_THRESHOLD

class SignalEngine:
    def __init__(self):
        pass

    def synthesize(self, technical_analysis: dict, news_analysis: dict) -> dict:
        """
        Synthesizes technical and news data into a composite signal.
        Weighting: Technical (40%), News Sentiment (30%), Volume (30%)
        """
        symbol = technical_analysis["symbol"]
        
        tech_score = technical_analysis.get("technical_score", 0.0)
        sentiment_score = 0.0
        headlines = []
        
        if news_analysis and symbol in news_analysis:
            sentiment_score = news_analysis[symbol].get("aggregated_score", 0.0)
            headlines = news_analysis[symbol].get("headlines", [])
            
        # Normalize volume to 0.0 - 1.0 (cap at 2x avg volume for scoring)
        vol_ratio = technical_analysis.get("volume_ratio", 0.0)
        vol_score = min(vol_ratio / 2.0, 1.0)
        
        # Composite score
        composite_score = (tech_score * 0.40) + (sentiment_score * 0.30) + (vol_score * 0.30)
        composite_score = round(composite_score, 2)
        
        # Determine Risk Rating based on composite
        if composite_score >= 0.70:
            risk_level = "LOW"
        elif composite_score >= 0.50:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
            
        return {
            "symbol": symbol,
            "composite_score": composite_score,
            "tech_score": tech_score,
            "sentiment_score": sentiment_score,
            "vol_score": round(vol_score, 2),
            "risk_level": risk_level,
            "technical_data": technical_analysis,
            "headlines": headlines
        }

    def filter_and_rank(self, signals: list, max_alerts: int = 5) -> list:
        """
        Filters out low-quality signals and ranks them by composite score.
        Returns top `max_alerts` signals.
        """
        # Filter minimum viability (Need either good technicals or good news)
        valid_signals = []
        for sig in signals:
            if sig["composite_score"] >= 0.40 or sig["sentiment_score"] >= SENTIMENT_THRESHOLD:
                valid_signals.append(sig)
                
        # Rank by composite score descending
        valid_signals.sort(key=lambda x: x["composite_score"], reverse=True)
        
        return valid_signals[:max_alerts]

if __name__ == "__main__":
    import json
    engine = SignalEngine()
    
    # Mock data
    ta_mock = {
        "symbol": "RELIANCE",
        "technical_score": 0.8,
        "volume_ratio": 1.5
    }
    
    news_mock = {
        "RELIANCE": {
            "aggregated_score": 0.6,
            "headlines": [{"title": "Reliance signs major deal"}]
        }
    }
    
    signal = engine.synthesize(ta_mock, news_mock)
    ranked = engine.filter_and_rank([signal])
    
    print(f"Top Signals:\n{json.dumps(ranked, indent=2)}")
