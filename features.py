"""
Feature engineering for stock recommendation.
Extracts technical and statistical features from historical stock data.
"""

import numpy as np
from typing import Dict, List


def calculate_moving_average(prices: List[float], window: int = 20) -> float:
    """
    Calculate moving average of prices.
    
    Args:
        prices: List of historical prices
        window: Number of periods for moving average
    
    Returns:
        Moving average value
    """
    if len(prices) < window:
        window = len(prices)
    
    return np.mean(prices[-window:]) if prices else 0.0


def calculate_volatility(prices: List[float], window: int = 20) -> float:
    """
    Calculate price volatility (standard deviation).
    
    Args:
        prices: List of historical prices
        window: Number of periods for volatility calculation
    
    Returns:
        Volatility (standard deviation)
    """
    if len(prices) < window:
        window = len(prices)
    
    if not prices or len(prices) < 2:
        return 0.0
    
    return np.std(prices[-window:])


def calculate_momentum(prices: List[float], period: int = 10) -> float:
    """
    Calculate price momentum (rate of change).
    
    Args:
        prices: List of historical prices
        period: Number of periods to calculate momentum
    
    Returns:
        Momentum value (positive = uptrend, negative = downtrend)
    """
    if len(prices) < period + 1:
        if len(prices) < 2:
            return 0.0
        period = len(prices) - 1
    
    current_price = prices[-1]
    past_price = prices[-(period + 1)]
    
    if past_price == 0:
        return 0.0
    
    return (current_price - past_price) / past_price


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: List of historical prices
        period: Number of periods for RSI calculation
    
    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral
    
    deltas = np.diff(prices[-period-1:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_price_strength(prices: List[float]) -> float:
    """
    Calculate overall price strength (trend direction).
    
    Args:
        prices: List of historical prices
    
    Returns:
        Strength value between -1 (strong downtrend) and 1 (strong uptrend)
    """
    if len(prices) < 2:
        return 0.0
    
    recent_prices = prices[-20:] if len(prices) >= 20 else prices
    
    # Calculate simple linear trend
    x = np.arange(len(recent_prices))
    y = np.array(recent_prices)
    
    # Fit line: slope indicates trend direction
    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]
    
    # Normalize slope to -1 to 1 range
    price_range = max(y) - min(y)
    if price_range == 0:
        return 0.0
    
    strength = (slope * len(y)) / price_range
    return max(-1.0, min(1.0, strength))


def extract_features(prices: List[float], news_sentiment: float = 0.0) -> Dict[str, float]:
    """
    Extract all technical features for the recommendation model.
    
    Args:
        prices: List of historical prices
        news_sentiment: Sentiment score from news analysis (-1 to 1)
    
    Returns:
        Dictionary of features for the model
    """
    if not prices or len(prices) < 5:
        return {
            'momentum': 0.0,
            'volatility': 0.0,
            'price_strength': 0.0,
            'rsi': 50.0,
            'news_sentiment': news_sentiment
        }
    
    return {
        'momentum': calculate_momentum(prices),
        'volatility': calculate_volatility(prices),
        'price_strength': calculate_price_strength(prices),
        'rsi': calculate_rsi(prices),
        'news_sentiment': news_sentiment
    }
