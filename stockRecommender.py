"""
Stock Buy/Sell/Hold Recommendation Engine
Uses scikit-learn to analyze historical stock data and news sentiment.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os

from features import extract_features
from sentiment import analyze_sentiment, aggregate_sentiments


class StockRecommender:
    """
    Machine learning-based stock recommendation system.
    Analyzes historical prices and news sentiment to suggest buy/sell/hold actions.
    """
    
    def __init__(self, model_path: str = 'stock_model.pkl'):
        """
        Initialize the stock recommender.
        
        Args:
            model_path: Path to load/save the trained model
        """
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = ['momentum', 'volatility', 'price_strength', 'rsi', 'news_sentiment']
        self.classes = ['sell', 'hold', 'buy']  # 0: sell, 1: hold, 2: buy
        
        # Load existing model if available
        if os.path.exists(model_path):
            self.load_model()
        else:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a new model with default parameters."""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        print("Initialized new Random Forest model")
    
    def train(self, training_data: List[Dict], labels: List[str]):
        """
        Train the model on historical stock data.
        
        Args:
            training_data: List of feature dictionaries
            labels: List of recommendation labels ('buy', 'hold', 'sell')
        """
        if not training_data or not labels:
            print("No training data provided")
            return
        
        # Convert to feature matrix
        X = np.array([
            [d.get(name, 0.0) for name in self.feature_names]
            for d in training_data
        ])
        
        # Convert labels to numeric
        y = np.array([self.classes.index(label) for label in labels])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        print(f"Trained model on {len(training_data)} samples")
        
        # Save model
        self.save_model()
    
    def recommend(self, 
                 prices: List[float],
                 news_headlines: Optional[List[str]] = None,
                 confidence_threshold: float = 0.5) -> Dict:
        """
        Get buy/sell/hold recommendation for a stock.
        
        Args:
            prices: List of historical prices (last 20-90 days recommended)
            news_headlines: Optional list of recent news headlines
            confidence_threshold: Minimum confidence to make a recommendation
        
        Returns:
            Dictionary with recommendation, confidence, and analysis details
        """
        if not prices or len(prices) < 5:
            return {
                'recommendation': 'hold',
                'confidence': 0.0,
                'reason': 'Insufficient historical data',
                'analysis': {}
            }
        
        # Analyze news sentiment
        news_sentiment = 0.0
        if news_headlines:
            sentiments = [analyze_sentiment(h)[0] for h in news_headlines]
            news_sentiment, _ = aggregate_sentiments(sentiments)
        
        # Extract features
        features = extract_features(prices, news_sentiment)
        
        # Prepare feature vector
        X = np.array([[features[name] for name in self.feature_names]])
        
        # Check if model and scaler are fitted before ML prediction
        if (self.model is None or 
            not hasattr(self.scaler, 'n_features_in_') or 
            not hasattr(self.model, 'classes_')):
            return self._get_rule_based_recommendation(features)
        
        # Scale features (safe now)
        X_scaled = self.scaler.transform(X)
        
        # Get prediction and probability
        
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        recommendation = self.classes[prediction]
        confidence = float(probabilities[prediction])
        
        # Apply confidence threshold
        if confidence < confidence_threshold:
            recommendation = 'hold'
            confidence = 0.5
        
        return {
            'recommendation': recommendation,
            'confidence': round(confidence, 3),
            'reason': self._generate_reason(features, recommendation),
            'analysis': {
                'momentum': round(features['momentum'], 3),
                'volatility': round(features['volatility'], 3),
                'price_strength': round(features['price_strength'], 3),
                'rsi': round(features['rsi'], 1),
                'news_sentiment': round(features['news_sentiment'], 3),
                'price_trend': 'uptrend' if features['price_strength'] > 0.2 else 'downtrend' if features['price_strength'] < -0.2 else 'neutral'
            }
        }
    
    def _get_rule_based_recommendation(self, features: Dict) -> Dict:
        """
        Generate recommendation using rule-based approach (when model not trained).
        
        Args:
            features: Feature dictionary
        
        Returns:
            Recommendation dictionary
        """
        momentum = features['momentum']
        rsi = features['rsi']
        price_strength = features['price_strength']
        sentiment = features['news_sentiment']
        
        # Rule-based logic
        buy_score = 0
        sell_score = 0
        
        # Momentum analysis
        if momentum > 0.05:
            buy_score += 1
        elif momentum < -0.05:
            sell_score += 1
        
        # RSI analysis (overbought/oversold)
        if rsi < 30:  # Oversold - potential buy
            buy_score += 1
        elif rsi > 70:  # Overbought - potential sell
            sell_score += 1
        
        # Price strength analysis
        if price_strength > 0.3:
            buy_score += 1
        elif price_strength < -0.3:
            sell_score += 1
        
        # Sentiment analysis
        if sentiment > 0.3:
            buy_score += 1
        elif sentiment < -0.3:
            sell_score += 1
        
        # Determine recommendation
        if buy_score > sell_score:
            recommendation = 'buy'
        elif sell_score > buy_score:
            recommendation = 'sell'
        else:
            recommendation = 'hold'
        
        confidence = max(buy_score, sell_score) / 4.0
        
        return {
            'recommendation': recommendation,
            'confidence': round(min(confidence, 0.95), 3),
            'reason': self._generate_reason(features, recommendation),
            'analysis': {
                'momentum': round(momentum, 3),
                'volatility': round(features['volatility'], 3),
                'price_strength': round(price_strength, 3),
                'rsi': round(rsi, 1),
                'news_sentiment': round(sentiment, 3),
                'price_trend': 'uptrend' if price_strength > 0.2 else 'downtrend' if price_strength < -0.2 else 'neutral'
            }
        }
    
    def _generate_reason(self, features: Dict, recommendation: str) -> str:
        """Generate a human-readable reason for the recommendation."""
        momentum = features['momentum']
        rsi = features['rsi']
        price_strength = features['price_strength']
        sentiment = features['news_sentiment']
        
        reasons = []
        
        if recommendation == 'buy':
            if momentum > 0:
                reasons.append("positive momentum")
            if rsi < 40:
                reasons.append("RSI indicates room to grow")
            if sentiment > 0:
                reasons.append("positive news sentiment")
            if price_strength > 0:
                reasons.append("uptrend detected")
        
        elif recommendation == 'sell':
            if momentum < 0:
                reasons.append("negative momentum")
            if rsi > 60:
                reasons.append("RSI shows overbought conditions")
            if sentiment < 0:
                reasons.append("negative news sentiment")
            if price_strength < 0:
                reasons.append("downtrend detected")
        
        else:  # hold
            reasons.append("mixed signals")
            if abs(momentum) < 0.05:
                reasons.append("neutral momentum")
            if 40 <= rsi <= 60:
                reasons.append("RSI in neutral zone")
        
        return "• " + ", ".join(reasons) if reasons else "Neutral market conditions"
    
    def save_model(self):
        """Save the trained model to disk."""
        if self.model is None:
            return
        
        try:
            data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'classes': self.classes
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(data, f)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self):
        """Load a trained model from disk."""
        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            print(f"Model loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self._initialize_model()


# Convenience functions for easy usage

def get_recommendation(prices: List[float],
                      news_headlines: Optional[List[str]] = None,
                      model_path: str = 'stock_model.pkl') -> Dict:
    """
    Quick function to get stock recommendation.
    
    Args:
        prices: Historical stock prices
        news_headlines: Recent news about the stock
        model_path: Path to the trained model
    
    Returns:
        Recommendation dictionary with details
    
    Example:
        >>> prices = [100, 101, 102, 103, 102, 104, 105]
        >>> recommendation = get_recommendation(prices)
        >>> print(recommendation['recommendation'])
        'buy'
    """
    recommender = StockRecommender(model_path)
    return recommender.recommend(prices, news_headlines)


if __name__ == '__main__':
    # Example usage
    print("Stock Recommender Module")
    print("=" * 50)
    
    # Example: Get recommendation for a stock
    example_prices = [100, 101, 102, 103, 102, 104, 105, 106, 107, 108]
    example_news = [
        "Company reports strong Q4 results",
        "Revenue exceeds analyst expectations",
        "Stock upgrades to buy rating"
    ]
    
    recommendation = get_recommendation(example_prices, example_news)
    
    print(f"Recommendation: {recommendation['recommendation'].upper()}")
    print(f"Confidence: {recommendation['confidence']:.0%}")
    print(f"Reason: {recommendation['reason']}")
    print("\nAnalysis Details:")
    for key, value in recommendation['analysis'].items():
        print(f"  {key}: {value}")
