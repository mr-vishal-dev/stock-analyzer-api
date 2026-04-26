from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from stockRecommender import get_recommendation
from data_fetcher import fetch_stock_data
from news_fetcher import get_latest_news
from news_fetcher import NewsAPIClient

app = FastAPI(title="Stock Recommender API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEWS_API_KEY = "3c550a7fcef74e20ae9698999d0ff4e1"

class RecommendationRequest(BaseModel):
    symbol: str
    period: Optional[str] = "3mo"

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Stock Recommender API"}

@app.post("/recommend")
async def get_recommendation_api(request: dict):
    try:
        symbol = request.get('symbol', '').upper()
        period = request.get('period', '3mo')
        
        print(f"Processing {symbol}...")
        
        # Fetch historical data
        prices, stock_info = fetch_stock_data(symbol, period=period)
        
        if not prices or len(prices) < 5:
            raise HTTPException(status_code=400, detail=f"Insufficient data for {symbol}")
        
        print(f"Fetched {len(prices)} prices")
        
        # Strip exchange suffix (e.g., .NS, .BO) for news search
        news_symbol = symbol.split('.')[0]
        company_name = stock_info.get('name', news_symbol)
        
        # Fetch news
        try:
            _, headlines = get_latest_news(news_symbol, company_name, NEWS_API_KEY)
        except:
            headlines = []
            print("Using empty headlines")
        
        print(f"Processing {len(headlines)} headlines")
        
        # Get ML recommendation
        recommendation = get_recommendation(prices, headlines)
        recommendation["symbol"] = symbol
        recommendation["stock_info"] = stock_info
        
        return recommendation
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

