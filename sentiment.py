"""
Simple sentiment analysis for news headlines.
Uses basic text features to score sentiment as positive, neutral, or negative.
"""

import re
from typing import Tuple

# Positive keywords for stocks
POSITIVE_KEYWORDS = {
    'gain', 'rally', 'surge', 'bullish', 'outperform', 'beat', 'upgrade',
    'profit', 'revenue', 'growth', 'strong', 'positive', 'jump', 'success',
    'expansion', 'record', 'rise', 'momentum', 'recovery', 'solid'
}

# Negative keywords for stocks
NEGATIVE_KEYWORDS = {
    'fall', 'decline', 'crash', 'bearish', 'underperform', 'miss', 'downgrade',
    'loss', 'loss', 'decline', 'weak', 'negative', 'drop', 'failure',
    'contraction', 'loss', 'decline', 'bear', 'recession', 'concerns', 'risk'
}

def analyze_sentiment(text: str) -> Tuple[float, str]:
    """
    Analyze sentiment of a news headline or text.
    
    Args:
        text: News headline or company news text
    
    Returns:
        Tuple of (sentiment_score, sentiment_label)
        sentiment_score: float between -1 (very negative) and 1 (very positive)
        sentiment_label: 'positive', 'neutral', or 'negative'
    """
    if not text:
        return 0.0, 'neutral'
    
    text_lower = text.lower()
    
    # Count positive and negative keywords
    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    
    # Calculate sentiment score
    total_keywords = positive_count + negative_count
    if total_keywords == 0:
        return 0.0, 'neutral'
    
    sentiment_score = (positive_count - negative_count) / total_keywords
    
    # Normalize to -1 to 1 range
    sentiment_score = max(-1.0, min(1.0, sentiment_score))
    
    # Determine label
    if sentiment_score > 0.2:
        label = 'positive'
    elif sentiment_score < -0.2:
        label = 'negative'
    else:
        label = 'neutral'
    
    return sentiment_score, label


def aggregate_sentiments(sentiments: list) -> Tuple[float, str]:
    """
    Aggregate multiple sentiment scores.
    
    Args:
        sentiments: List of sentiment scores
    
    Returns:
        Tuple of (average_sentiment, label)
    """
    if not sentiments:
        return 0.0, 'neutral'
    
    avg = sum(sentiments) / len(sentiments)
    avg = max(-1.0, min(1.0, avg))
    
    if avg > 0.2:
        label = 'positive'
    elif avg < -0.2:
        label = 'negative'
    else:
        label = 'neutral'
    
    return avg, label
