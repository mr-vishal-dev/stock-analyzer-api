"""
Stock Recommendation Module
Provides buy/sell/hold recommendations using scikit-learn
"""

from .stockRecommender import StockRecommender, get_recommendation
from .features import extract_features
from .sentiment import analyze_sentiment, aggregate_sentiments

__version__ = '1.0.0'
__all__ = [
    'StockRecommender',
    'get_recommendation',
    'extract_features',
    'analyze_sentiment',
    'aggregate_sentiments'
]
