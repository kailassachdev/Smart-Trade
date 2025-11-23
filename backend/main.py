from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import random
import threading
import time
import yfinance as yf
from datetime import datetime
from ollama_service import OllamaService

app = FastAPI(title="Smart Trade API")

# Initialize Ollama Service
# Ensure you have run 'ollama pull llama3.2'
ollama_service = OllamaService(model="deepseek-v3.1:671b-cloud")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Data Storage
portfolio_data = {
    "cash": 100000.0,
    "equity": 0.0,
    "portfolio_value": 100000.0,
    "positions": []
}

trade_logs = []

# Agent Control
agent_running = False
agent_thread = None

class TradeLog(BaseModel):
    id: int
    timestamp: str
    symbol: str
    action: str
    quantity: int
    price: float
    reason: str

class MarketData(BaseModel):
    symbol: str
    price: float
    trends: Optional[dict] = None

@app.get("/")
def read_root():
    return {"status": "Smart Trade API is running"}

@app.get("/portfolio")
def get_portfolio():
    # In a real app, fetch from Alpaca API
    return portfolio_data

@app.get("/trade-logs", response_model=List[TradeLog])
def get_trade_logs():
    return trade_logs

@app.post("/api/analyze")
def analyze_market(data: MarketData):
    analysis = ollama_service.analyze_market(data.dict())
    return {"analysis": analysis}

def execute_trade_logic():
    """Core logic to generate a trade using real market data."""
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "BTC-USD", "ETH-USD"]
    symbol = random.choice(symbols)
    
    try:
        # Fetch real data
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        
        if data.empty:
            raise Exception("No data found")
            
        current_price = data['Close'].iloc[-1]
        open_price = data['Open'].iloc[-1]
        price_change = current_price - open_price
        change_pct = (price_change / open_price) * 100
        
        price = round(current_price, 2)
        
        # Simple strategy for demo: Buy if up, Sell if down (randomized slightly)
        # In reality, the AI should decide this, but we'll pre-select for the prompt context
        action = "BUY" if change_pct > 0 else "SELL"
        if random.random() < 0.2: # 20% chance to go against trend for variety
            action = "SELL" if action == "BUY" else "BUY"
            
        quantity = random.randint(1, 5)
        
        market_context = {
            "symbol": symbol,
            "price": f"${price}",
            "daily_change": f"{change_pct:.2f}%",
            "action": action, # Suggesting an action to the AI to justify
            "technical_indicators": f"Price is {'up' if change_pct > 0 else 'down'} {abs(change_pct):.2f}% today."
        }
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        # Fallback to random data if API fails
        action = random.choice(["BUY", "SELL"])
        price = round(random.uniform(100, 1000), 2)
        quantity = random.randint(1, 10)
        market_context = {
            "symbol": symbol,
            "price": price,
            "action": action,
            "note": "Real data unavailable, using simulation."
        }

    reason = ollama_service.analyze_market(market_context)
    if "Error" in reason:
        reason = "Simulated decision based on moving average strategy (Ollama unavailable)."
    
    log = {
        "id": len(trade_logs) + 1,
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "action": action,
        "quantity": quantity,
        "price": price,
        "reason": reason
    }
    trade_logs.append(log)
    
    # Update portfolio mock
    cost = price * quantity
    if action == "BUY":
        if portfolio_data["cash"] >= cost:
            portfolio_data["cash"] -= cost
            portfolio_data["equity"] += cost
            portfolio_data["positions"].append({"symbol": symbol, "qty": quantity, "avg_entry_price": price})
    
    portfolio_data["portfolio_value"] = portfolio_data["cash"] + portfolio_data["equity"]
    
    return log

def run_agent_loop():
    global agent_running
    print("Agent loop started")
    while agent_running:
        try:
            print("Agent executing trade...")
            execute_trade_logic()
            time.sleep(10)  # Trade every 10 seconds
        except Exception as e:
            print(f"Error in agent loop: {e}")
            time.sleep(5)
    print("Agent loop stopped")

@app.post("/start-agent")
def start_agent():
    global agent_running, agent_thread
    if not agent_running:
        agent_running = True
        agent_thread = threading.Thread(target=run_agent_loop)
        agent_thread.daemon = True
        agent_thread.start()
        return {"status": "Agent started"}
    return {"status": "Agent already running"}

@app.post("/stop-agent")
def stop_agent():
    global agent_running
    agent_running = False
    return {"status": "Agent stopping..."}

# Simulation endpoint for demo purposes
@app.post("/simulate-trade")
def simulate_trade():
    return execute_trade_logic()
