"""
Fetch news about companies using NewsAPI
"""

import requests
from typing import List, Dict, Optional
import os


class NewsAPIClient:
    """Client for NewsAPI.org"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize NewsAPI client
        
        Args:
            api_key: NewsAPI key (get free one at https://newsapi.org)
                    If not provided, will look for NEWSAPI_KEY environment variable
        """
        self.api_key = api_key or os.getenv('NEWSAPI_KEY', '')
        self.base_url = 'https://newsapi.org/v2'
        
        if not self.api_key:
            print("⚠️  Warning: NewsAPI key not provided")
            print("   Get a free key at https://newsapi.org/")
            print("   Set NEWSAPI_KEY environment variable or pass api_key parameter")
    
    def search_news(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for news about a stock/company
        
        Args:
            query: Search query (company name or stock symbol)
            limit: Maximum number of articles to return
        
        Returns:
            List of news articles with headline, source, and date
        """
        if not self.api_key:
            print("⚠️  NewsAPI key not configured. Using demo news.")
            return self._get_demo_news(query)
        
        try:
            endpoint = f'{self.base_url}/everything'
            params = {
                'q': query,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': limit,
                'apiKey': self.api_key
            }
            
            print(f"Fetching news for '{query}'...")
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 401:
                print("❌ Invalid NewsAPI key")
                return self._get_demo_news(query)
            
            if response.status_code != 200:
                print(f"⚠️  NewsAPI error: {response.status_code}")
                return self._get_demo_news(query)
            
            data = response.json()
            
            if data.get('status') != 'ok':
                print(f"⚠️  API error: {data.get('message', 'Unknown error')}")
                return self._get_demo_news(query)
            
            articles = data.get('articles', [])
            
            # Format articles
            formatted = []
            for article in articles[:limit]:
                formatted.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'content': article.get('content', '')
                })
            
            print(f"✓ Retrieved {len(formatted)} articles")
            return formatted
        
        except requests.exceptions.Timeout:
            print("⚠️  Request timeout. Using demo news.")
            return self._get_demo_news(query)
        except Exception as e:
            print(f"⚠️  Error fetching news: {e}")
            return self._get_demo_news(query)
    
    def _get_demo_news(self, query: str) -> List[Dict]:
        """Get demo news when API is unavailable"""
        demo_articles = {
            'infy': [
                {
                    'title': 'Infosys reports strong Q4 results beating expectations',
                    'description': 'Infosys delivered robust financial results with revenue growth exceeding analyst expectations.',
                    'source': 'Financial Times',
                    'url': '#',
                    'published_at': '2024-01-20',
                    'content': 'Strong performance'
                },
                {
                    'title': 'Infosys to expand digital services in 2024',
                    'description': 'Company announces significant investment in digital transformation services.',
                    'source': 'Reuters',
                    'url': '#',
                    'published_at': '2024-01-18',
                    'content': 'Expansion plans'
                },
                {
                    'title': 'Infosys upgrades full-year guidance',
                    'description': 'Strong demand for IT services leads to optimistic outlook.',
                    'source': 'Bloomberg',
                    'url': '#',
                    'published_at': '2024-01-15',
                    'content': 'Positive outlook'
                },
            ],
            'tcs': [
                {
                    'title': 'TCS reports record profit margins',
                    'description': 'Tata Consultancy Services achieves highest profit in company history.',
                    'source': 'Economic Times',
                    'url': '#',
                    'published_at': '2024-01-20',
                    'content': 'Record performance'
                },
                {
                    'title': 'TCS to hire 40,000 employees in 2024',
                    'description': 'Major hiring drive indicates strong business momentum.',
                    'source': 'Times of India',
                    'url': '#',
                    'published_at': '2024-01-17',
                    'content': 'Growth plans'
                },
            ],
            'default': [
                {
                    'title': f'{query} shows strong performance',
                    'description': 'Company delivers results exceeding expectations.',
                    'source': 'Business News',
                    'url': '#',
                    'published_at': '2024-01-20',
                    'content': 'Positive news'
                },
                {
                    'title': f'Analysts remain bullish on {query}',
                    'description': 'Research firms maintain buy ratings.',
                    'source': 'Market News',
                    'url': '#',
                    'published_at': '2024-01-18',
                    'content': 'Bullish sentiment'
                },
            ]
        }
        
        # Match query to demo data
        query_lower = query.lower()
        articles = None
        
        if 'infy' in query_lower or 'infosys' in query_lower:
            articles = demo_articles['infy']
        elif 'tcs' in query_lower or 'consultancy' in query_lower:
            articles = demo_articles['tcs']
        else:
            articles = demo_articles['default']
        
        print(f"⚠️  Using demo news for '{query}'")
        return articles


def extract_headlines(articles: List[Dict]) -> List[str]:
    """
    Extract headlines and description from articles
    
    Args:
        articles: List of article dictionaries
    
    Returns:
        List of headlines and descriptions combined
    """
    headlines = []
    for article in articles:
        title = article.get('title', '').strip() if article.get('title') else ''
        description = article.get('description', '').strip() if article.get('description') else ''
        
        # Combine title and description for better sentiment
        combined = (title + ' ' + description).strip()
        
        if combined:
            headlines.append(combined)
    
    return headlines


def get_latest_news(symbol: str, company_name: str = '', api_key: str = None, limit: int = 10) -> tuple:
    """
    Convenience function to get latest news for a stock
    
    Args:
        symbol: Stock symbol
        company_name: Full company name (optional)
        api_key: NewsAPI key
        limit: Number of articles
    
    Returns:
        Tuple of (articles, headlines)
    """
    client = NewsAPIClient(api_key=api_key)
    
    # Try both symbol and company name
    query = f"{company_name} {symbol}".strip() if company_name else symbol
    articles = client.search_news(query, limit=limit)
    
    headlines = extract_headlines(articles)
    
    return articles, headlines


if __name__ == '__main__':
    # Example usage
    print("NewsAPI Client Test")
    print("=" * 50)
    
    client = NewsAPIClient()
    
    # Search for news
    articles = client.search_news('Infosys', limit=5)
    
    print("\nArticles found:")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Date: {article['published_at']}")
