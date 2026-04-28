from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from stockRecommender import get_recommendation
from data_fetcher import fetch_stock_data
from news_fetcher import get_latest_news
from news_fetcher import NewsAPIClient
from features import (
    extract_features, 
    calculate_moving_average, 
    calculate_volatility, 
    calculate_momentum,
    calculate_rsi,
    calculate_price_strength
)
from sentiment import analyze_sentiment, aggregate_sentiments

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
async def get_recommendation_api(request: RecommendationRequest):
    try:
        symbol = request.symbol.upper()
        period = request.period
        
        print(f"Processing {symbol}...")
        
        # Fetch historical data
        prices, stock_info = fetch_stock_data(symbol, period=period)
        if not prices:
            raise HTTPException(status_code=400,detail=f"Stock data unavailable for {symbol} (Yahoo blocked or failed)")
       
        if not prices or len(prices) < 5:
             raise HTTPException(status_code=400,detail=f"Stock data unavailable or insufficient for {symbol}")
        
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


# ============================================
# TEST ALL MODULES AT ONCE
# ============================================

@app.get("/test/all")
async def test_all_modules(symbol: str = "AAPL", period: str = "1mo"):
    """
    Test all modules at once and return separate responses for each module.
    """
    try:
        print(f"[TEST ALL] Testing all modules for {symbol}...")
        
        results = {}
        
        # =====================
        # 1. TEST DATA_FETCHER
        # =====================
        print("[TEST ALL] Testing data_fetcher...")
        try:
            prices, stock_info = fetch_stock_data(symbol, period=period)
            results["data_fetcher"] = {
                "status": "success",
                "message": "data_fetcher module working",
                "data": {
                    "symbol": symbol,
                    "period": period,
                    "prices_count": len(prices),
                    "prices_sample": prices[:5] if prices else [],
                    "stock_info": stock_info
                }
            }
        except Exception as e:
            results["data_fetcher"] = {
                "status": "error",
                "message": f"data_fetcher error: {str(e)}",
                "data": None
            }
        
        # =====================
        # 2. TEST FEATURES
        # =====================
        print("[TEST ALL] Testing features...")
        try:
            if prices and len(prices) >= 5:
                ma_20 = calculate_moving_average(prices, window=20)
                ma_50 = calculate_moving_average(prices, window=50) if len(prices) >= 50 else None
                volatility = calculate_volatility(prices, window=20)
                momentum = calculate_momentum(prices, period=10)
                rsi = calculate_rsi(prices, period=14)
                price_strength = calculate_price_strength(prices)
                all_features = extract_features(prices)
                
                results["features"] = {
                    "status": "success",
                    "message": "features module working",
                    "data": {
                        "moving_average_20": round(ma_20, 2),
                        "moving_average_50": round(ma_50, 2) if ma_50 else None,
                        "volatility": round(volatility, 4),
                        "momentum": round(momentum, 4),
                        "rsi": round(rsi, 2),
                        "price_strength": round(price_strength, 4),
                        "extracted_features": all_features
                    }
                }
            else:
                results["features"] = {
                    "status": "error",
                    "message": "Insufficient price data",
                    "data": None
                }
        except Exception as e:
            results["features"] = {
                "status": "error",
                "message": f"features error: {str(e)}",
                "data": None
            }
        
        # =====================
        # 3. TEST NEWS_FETCHER
        # =====================
        print("[TEST ALL] Testing news_fetcher...")
        try:
            news_symbol = symbol.split('.')[0]
            company_name = stock_info.get('name', news_symbol) if stock_info else symbol
            articles, headlines = get_latest_news(news_symbol, company_name, NEWS_API_KEY)
            
            results["news_fetcher"] = {
                "status": "success",
                "message": "news_fetcher module working",
                "data": {
                    "symbol": news_symbol,
                    "company": company_name,
                    "articles_count": len(articles),
                    "headlines_count": len(headlines),
                    "articles": articles[:3] if articles else [],
                    "headlines": headlines[:5] if headlines else []
                }
            }
        except Exception as e:
            results["news_fetcher"] = {
                "status": "error",
                "message": f"news_fetcher error: {str(e)}",
                "data": None
            }
        
        # =====================
        # 4. TEST SENTIMENT
        # =====================
        print("[TEST ALL] Testing sentiment...")
        try:
            test_headlines = [
                "Stock rallies on strong earnings",
                "Company reports loss",
                "Market shows positive trend",
                "Concerns about recession",
                "Bullish outlook from analysts"
            ]
            
            headline_results = []
            for hl in test_headlines:
                score, label = analyze_sentiment(hl)
                headline_results.append({
                    "headline": hl,
                    "score": round(score, 4),
                    "label": label
                })
            
            sentiment_scores = [h["score"] for h in headline_results]
            aggregated_score, aggregated_label = aggregate_sentiments(sentiment_scores)
            
            results["sentiment"] = {
                "status": "success",
                "message": "sentiment module working",
                "data": {
                    "test_headlines": headline_results,
                    "aggregated_score": round(aggregated_score, 4),
                    "aggregated_label": aggregated_label
                }
            }
        except Exception as e:
            results["sentiment"] = {
                "status": "error",
                "message": f"sentiment error: {str(e)}",
                "data": None
            }
        
        # =====================
        # 5. TEST STOCK_RECOMMENDER
        # =====================
        print("[TEST ALL] Testing stock_recommender...")
        try:
            if prices and len(prices) >= 5:
                # Get news for recommendation
                news_symbol = symbol.split('.')[0]
                company_name = stock_info.get('name', news_symbol) if stock_info else symbol
                _, headlines = get_latest_news(news_symbol, company_name, NEWS_API_KEY)
                
                recommendation = get_recommendation(prices, headlines)
                
                results["stock_recommender"] = {
                    "status": "success",
                    "message": "stock_recommender module working",
                    "data": {
                        "symbol": symbol,
                        "prices_used": len(prices),
                        "headlines_analyzed": len(headlines),
                        "recommendation": recommendation
                    }
                }
            else:
                results["stock_recommender"] = {
                    "status": "error",
                    "message": "Insufficient price data for recommendation",
                    "data": None
                }
        except Exception as e:
            results["stock_recommender"] = {
                "status": "error",
                "message": f"stock_recommender error: {str(e)}",
                "data": None
            }
        
        # =====================
        # SUMMARY
        # =====================
        success_count = sum(1 for m in results.values() if m["status"] == "success")
        total_count = len(results)
        
        return {
            "summary": {
                "status": "completed",
                "symbol": symbol,
                "period": period,
                "modules_tested": total_count,
                "modules_passed": success_count,
                "modules_failed": total_count - success_count
            },
            "modules": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test all error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

