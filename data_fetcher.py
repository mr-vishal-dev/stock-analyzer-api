"""
Fetch historical stock data - uses yfinance as primary source
"""

import os
import requests
from typing import List, Tuple, Optional
import yfinance as yf

# AlphaVantage API Key - optional, used as backup
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
if not ALPHA_VANTAGE_API_KEY:
    print("⚠️  ALPHA_VANTAGE_API_KEY not set - using yfinance only")

BASE_URL = "https://www.alphavantage.co/query"


def fetch_with_yfinance(symbol: str, period: str = '3mo') -> Tuple[List[float], dict]:
    """
    Fallback: Fetch stock data using yfinance.
    
    Args:
        symbol: Stock symbol (e.g., 'INFY', 'AAPL', 'GOOGL')
        period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y')
    
    Returns:
        Tuple of (prices_list, stock_info_dict)
    """
    try:
        print(f"[yfinance] Fetching {symbol} data...")
        ticker = yf.Ticker(symbol)
        
        # Map period to yfinance period
        period_map = {
            '1d': '1d',
            '5d': '5d',
            '1mo': '1mo',
            '3mo': '3mo',
            '6mo': '6mo',
            '1y': '1y',
            '2y': '2y',
            '5y': '5y',
        }
        yf_period = period_map.get(period, '3mo')
        
        hist = ticker.history(period=yf_period)
        
        print(f"[yfinance] Raw data shape: {hist.shape if hasattr(hist, 'shape') else 'N/A'}")
        print(f"[yfinance] Raw data columns: {list(hist.columns) if hasattr(hist, 'columns') else 'N/A'}")
        
        if hist.empty:
            print(f"[yfinance] No data for {symbol} - trying with explicit dates...")
            # Try with explicit date range
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            hist = ticker.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
            print(f"[yfinance] Retry data shape: {hist.shape if hasattr(hist, 'shape') else 'N/A'}")
        
        if hist.empty:
            print(f"[yfinance] Still no data for {symbol}")
            return [], {}
        
        # Extract closing prices
        prices = hist['Close'].tolist()
        
        print(f"[yfinance] Extracted {len(prices)} prices")
        
        # Get stock info
        stock_info = {
            'name': ticker.info.get('shortName', symbol),
            'sector': ticker.info.get('sector', ''),
            'industry': ticker.info.get('industry', ''),
        }
        
        print(f"[yfinance] Retrieved {len(prices)} data points for {symbol}")
        return prices, stock_info
        
    except Exception as e:
        import traceback
        print(f"[yfinance] Error: {e}")
        print(f"[yfinance] Traceback: {traceback.format_exc()}")
        return [], {}


def fetch_stock_data(symbol: str, period: str = '3mo', interval: str = '1d') -> Tuple[List[float], dict]:
    """
    Fetch historical stock data - uses yfinance as primary source
    
    Args:
        symbol: Stock symbol (e.g., 'INFY', 'AAPL', 'GOOGL')
        period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y') - filters actual days
        interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo') - not used
    
    Returns:
        Tuple of (prices_list, stock_info_dict)
        prices_list: List of closing prices in chronological order
        stock_info_dict: Dictionary with stock info (name, sector, etc.)
    """
    # Try yfinance first (more reliable, no rate limits)
    print(f"Fetching {symbol} data via yfinance...")
    prices, stock_info = fetch_with_yfinance(symbol, period)
    
    # Use demo data if insufficient prices (less than 5)
    if not prices or len(prices) < 5:
        print(f"⚠️ Insufficient data from yfinance ({len(prices) if prices else 0} prices), trying AlphaVantage...")
        
        # Fallback to AlphaVantage if yfinance fails
        if ALPHA_VANTAGE_API_KEY:
            try:
                prices_av, stock_info_av = fetch_from_alpha_vantage(symbol, period)
                if prices_av and len(prices_av) >= 5:
                    return prices_av, stock_info_av
            except Exception as e:
                print(f"AlphaVantage fallback failed: {e}")
        
        # Return demo data as last resort
        print(f"⚠️ All data sources failed for {symbol}, using demo data")
        return get_demo_data(symbol)
    
    return prices, stock_info


def get_demo_data(symbol: str) -> Tuple[List[float], dict]:
    """
    Generate demo stock data for testing when all APIs fail.
    """
    import random
    import numpy as np
    
    # Base prices for common symbols
    base_prices = {
        'IBM': 180.0, 'AAPL': 175.0, 'GOOGL': 140.0, 'MSFT': 380.0,
        'AMZN': 180.0, 'TSLA': 200.0, 'META': 500.0, 'NVDA': 800.0,
        'INFY': 1500.0, 'TCS': 3500.0
    }
    
    base_price = base_prices.get(symbol.upper(), 100.0)
    
    # Generate realistic price movement
    np.random.seed(hash(symbol) % 2**32)
    returns = np.random.normal(0.0005, 0.02, 60)  # 60 days
    prices = [base_price]
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    
    stock_info = {
        'name': symbol.upper(),
        'sector': 'Technology',
        'industry': 'Information Technology',
        'is_demo': True
    }
    
    print(f"[DEMO] Generated {len(prices)} demo prices for {symbol}")
    return prices, stock_info


def fetch_from_alpha_vantage(symbol: str, period: str = '3mo') -> Tuple[List[float], dict]:
    """
    Fetch historical stock data from AlphaVantage API (backup method)
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
        print(f"DEBUG: Response keys: {list(data.keys())}")
        
        # Check for rate limit or errors
        if "Note" in data:
            print("⚠️ Rate limit hit - AlphaVantage free tier limit")
            print(f"DEBUG: Rate limit message: {data.get('Note')}")
            return [], {"error": "rate_limit", "message": data.get("Note", "Rate limit exceeded")}
        if "Error Message" in data:
            print(f"⚠️ API Error: {data.get('Error Message')}")
            return [], {"error": "api_error", "message": data.get("Error Message")}
        
        # Find the time series key dynamically
        time_series = {}
        for key in data.keys():
            if "Time Series" in key or "time" in key.lower():
                if isinstance(data[key], dict):
                    time_series = data[key]
                    print(f"DEBUG: Found time series with key: {key}")
                    break
        
        if not time_series:
            print(f"⚠️ No time series data for {symbol} from AlphaVantage")
            print(f"DEBUG: Full response: {data}")
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
        print(f"❌ Error fetching stock data from AlphaVantage: {e}")
        return [], {}


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
        
        # Debug: Print response keys
        print(f"DEBUG get_stock_info: Response keys: {list(data.keys())}")
        
        if not data or "Error Message" in data:
            print(f"DEBUG get_stock_info: Error or empty: {data}")
            return {'name': symbol}
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
