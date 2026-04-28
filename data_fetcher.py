"""
Fetch historical stock data from AlphaVantage API
"""

import os
import requests
from typing import List, Tuple, Optional

# AlphaVantage API Key - MUST be set in environment variables
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
if not ALPHA_VANTAGE_API_KEY:
    raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set!")

BASE_URL = "https://www.alphavantage.co/query"


def fetch_stock_data(symbol: str, period: str = '3mo', interval: str = '1d') -> Tuple[List[float], dict]:
    """
    Fetch historical stock data from AlphaVantage API
    
    Args:
        symbol: Stock symbol (e.g., 'INFY', 'AAPL', 'GOOGL')
        period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y') - filters actual days
        interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo') - not used
    
    Returns:
        Tuple of (prices_list, stock_info_dict)
        prices_list: List of closing prices in chronological order
        stock_info_dict: Dictionary with stock info (name, sector, etc.)
    """
    try:
        print(f"Fetching {symbol} data from AlphaVantage...")
        
        # Map period to number of trading days
        period_days = {
            '1d': 1,
            '5d': 5,
            '1mo': 22,    # ~22 trading days per month
            '3mo': 66,    # ~22 * 3 months
            '6mo': 132,   # ~22 * 6 months
            '1y': 252,    # ~252 trading days per year
            '2y': 504,
            '5y': 1260,
        }
        
        # Get the number of days to fetch
        days_to_fetch = period_days.get(period, 66)  # default to 3mo
        
        # Use compact for small requests, full for larger
        outputsize = "compact" if days_to_fetch <= 100 else "full"
        
        # Fetch daily time series
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params, timeout=30)
        data = response.json()
        
        # Debug: Print first few keys of response
        print(f"DEBUG: Response keys: {list(data.keys())[:5]}")
        
        # Check for rate limit or errors
        if "Note" in data:
            print("⚠️ Rate limit hit - AlphaVantage free tier limit")
            return [], {}
        if "Error Message" in data:
            print(f"⚠️ API Error: {data.get('Error Message')}")
            return [], {}
        
        time_series = data.get("Time Series (Daily)", {})
        
        if not time_series:
            print(f"⚠️ No data for {symbol}")
            print(f"DEBUG: Available keys: {list(data.keys())}")
            return [], {}
        
        # Extract closing prices (in chronological order)
        all_prices = [
            (date, float(day["4. close"]))
            for date, day in time_series.items()
        ]
        all_prices.sort(key=lambda x: x[0])  # Sort by date ascending
        
        # Filter by period (number of days)
        prices = [price for _, price in all_prices[-days_to_fetch:]]
        
        # Get stock info from OVERVIEW endpoint
        stock_info = get_stock_info(symbol)
        
        print(f"✓ Retrieved {len(prices)} data points for {symbol} (period: {period}, days: {days_to_fetch})")
        
        return prices, stock_info
    
    except Exception as e:
        print(f"❌ Error fetching stock data: {e}")
        raise


def get_current_price(symbol: str) -> Optional[float]:
    """
    Get current stock price using AlphaVantage GLOBAL_QUOTE
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Current price or None if error
    """
    try:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params, timeout=30)
        data = response.json()
        
        quote = data.get("Global Quote", {})
        if quote and "05. price" in quote:
            return float(quote["05. price"])
    
    except Exception as e:
        print(f"Error getting current price: {e}")
    
    return None


def get_stock_info(symbol: str) -> dict:
    """
    Get comprehensive stock information from AlphaVantage OVERVIEW endpoint
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Dictionary with stock info
    """
    try:
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params, timeout=30)
        data = response.json()
        
        if not data or "Error Message" in data:
            return {'name': symbol}
        
        # Map AlphaVantage fields to our stock_info format
        stock_info = {
            'name': data.get('Name', symbol),
            'sector': data.get('Sector', 'N/A'),
            'industry': data.get('Industry', 'N/A'),
            'country': data.get('Country', 'N/A'),
            'currency': data.get('Currency', 'USD'),
            'market_cap': data.get('MarketCapitalization', 'N/A'),
            'pe_ratio': data.get('PERatio', 'N/A'),
            'dividend_yield': data.get('DividendYield', 'N/A'),
            'fifty_two_week_high': data.get('52WeekHigh', 'N/A'),
            'fifty_two_week_low': data.get('52WeekLow', 'N/A'),
            'description': data.get('Description', ''),
            'exchange': data.get('Exchange', 'N/A'),
            'ceo': data.get('CEO', 'N/A'),
            'website': data.get('Website', 'N/A'),
        }
        
        return stock_info
    
    except Exception as e:
        print(f"Error getting stock info: {e}")
        return {'name': symbol}
