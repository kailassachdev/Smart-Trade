"""
routers/portfolio.py
--------------------
Portfolio and market data endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import yfinance as yf

import models
from database import get_db
from routers.auth import get_current_user

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio")
def get_portfolio(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet    = current_user.wallet
    positions = current_user.positions

    equity = 0.0
    formatted_positions = []

    for pos in positions:
        try:
            # Use average_price as current value for speed; in prod, cache yfinance data
            current_price = float(pos.average_price)
            pos_value     = current_price * pos.quantity
            equity       += pos_value
            formatted_positions.append({
                "symbol":          pos.symbol,
                "qty":             pos.quantity,
                "avg_entry_price": float(pos.average_price),
                "current_price":   current_price,
            })
        except Exception:
            pass

    cash = float(wallet.balance) if wallet else 0.0
    return {
        "cash":            cash,
        "equity":          equity,
        "portfolio_value": cash + equity,
        "positions":       formatted_positions,
    }


@router.get("/stock/{symbol}/history")
def get_stock_history(symbol: str, period: str = "1mo", interval: str = "1d"):
    """Fetch historical OHLCV data for charting via yfinance."""
    try:
        ticker = yf.Ticker(symbol.upper())
        data   = ticker.history(period=period, interval=interval)
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol '{symbol}'")

        result = []
        for index, row in data.iterrows():
            label = (
                index.strftime("%Y-%m-%d %H:%M:%S") if interval != "1d"
                else index.strftime("%Y-%m-%d")
            )
            result.append({"time": label, "value": round(float(row["Close"]), 2)})
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
