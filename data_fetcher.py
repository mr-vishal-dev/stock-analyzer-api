"""
Fetch historical stock data from Yahoo Finance (yfinance)
"""

import yfinance as yf
from typing import List, Tuple, Optional


def fetch_stock_data(symbol: str, period: str = '3mo', interval: str = '1d') -> Tuple[List[float], dict]:
    """
    Fetch historical stock data from Yahoo Finance
    
    Args:
        symbol: Stock symbol (e.g., 'INFY.NS', 'AAPL', 'GOOGL')
        period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max')
        interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
    
    Returns:
        Tuple of (prices_list, stock_info_dict)
        prices_list: List of closing prices in chronological order
        stock_info_dict: Dictionary with stock info (name, sector, etc.)
    """
    try:
        print(f"Fetching {symbol} data from Yahoo Finance...")
        
        # Download stock data
        ticker = yf.Ticker(symbol)
        # hist = ticker.history(period=period, interval=interval)
        hist = yf.download(
                    symbol,
                    period=period,
                    interval=interval,
                    progress=False,
                    threads=False
                    )
        if hist.empty:
            print(f"⚠️ No data for {symbol}")
            return [], {}
        # if hist.empty:
        #     raise ValueError(f"No data found for symbol: {symbol}")
        
        # Extract closing prices
        prices = hist['Close'].tolist()
        
        # Get stock info
        try:
            info = ticker.info
            stock_info = {
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'N/A'),
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
            }
        except:
            stock_info = {'name': symbol}
        
        print(f"✓ Retrieved {len(prices)} data points for {symbol}")
        
        return prices, stock_info
    
    except Exception as e:
        print(f"❌ Error fetching stock data: {e}")
        raise


def get_current_price(symbol: str) -> Optional[float]:
    """
    Get current stock price
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Current price or None if error
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        print(f"Error getting current price: {e}")
    
    return None


def get_stock_info(symbol: str) -> dict:
    """
    Get comprehensive stock information
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Dictionary with stock info
    """
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info
    except Exception as e:
        print(f"Error getting stock info: {e}")
        return {}
