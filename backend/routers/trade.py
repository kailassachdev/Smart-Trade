"""
routers/trade.py
----------------
Manual trade endpoints: buy, sell, trade-logs.

ARCHITECTURAL IMPROVEMENTS:
- #2: Atomic transactions with SELECT FOR UPDATE on wallet to prevent double-spending
- #5: Risk management checks run BEFORE any trade is committed
- #8: Structured logging for every trade execution
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import yfinance as yf

import models
from database import get_db
from routers.auth import get_current_user
from risk import risk_manager
from logging_config import get_logger, TRADE_EXECUTED, TRADE_SKIPPED, RISK_BLOCKED

log = get_logger("trade")
router = APIRouter(prefix="/trade", tags=["trade"])


class TradeAction(BaseModel):
    symbol: str
    quantity: int


def _fetch_current_price(symbol: str) -> float:
    """Fetch latest close price from yfinance. Raises HTTPException on failure."""
    try:
        ticker = yf.Ticker(symbol.upper())
        data = ticker.history(period="1d")
        if data.empty:
            raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")
        return float(data["Close"].iloc[-1])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching market data: {e}")


@router.post("/buy")
def buy_stock(trade: TradeAction, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if trade.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    symbol = trade.symbol.upper()
    current_price = _fetch_current_price(symbol)
    total_cost = current_price * trade.quantity

    # ── IMPROVEMENT #5: Risk checks before touching the database ──────────────
    risk_result = risk_manager.validate_buy(current_user, symbol, trade.quantity, current_price, db)
    if not risk_result.approved:
        log.warning(RISK_BLOCKED, user_id=current_user.id, symbol=symbol,
                    action="BUY", reason=risk_result.reason)
        raise HTTPException(status_code=400, detail=risk_result.reason)

    try:
        # IMPROVEMENT #2: Lock wallet row — prevents concurrent spend of same funds
        from database import IS_SQLITE
        wallet_query = db.query(models.Wallet).filter(models.Wallet.user_id == current_user.id)
        if not IS_SQLITE:
            wallet_query = wallet_query.with_for_update()
            
        wallet = wallet_query.first()
        if not wallet or float(wallet.balance) < total_cost:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient funds. Need ${total_cost:.2f}, have ${float(wallet.balance) if wallet else 0:.2f}"
            )

        wallet.balance = float(wallet.balance) - total_cost

        # Update or create position
        position = db.query(models.Position).filter(
            models.Position.user_id == current_user.id,
            models.Position.symbol == symbol
        ).first()

        if position:
            total_value = (float(position.quantity) * float(position.average_price)) + total_cost
            position.quantity     += trade.quantity
            position.average_price = total_value / position.quantity
        else:
            position = models.Position(
                user_id=current_user.id, symbol=symbol,
                quantity=trade.quantity, average_price=current_price
            )
            db.add(position)

        db.add(models.Transaction(
            user_id=current_user.id, symbol=symbol, action="BUY",
            quantity=trade.quantity, price=current_price,
            reason="Manual buy order"
        ))
        db.commit()

        log.info(TRADE_EXECUTED, user_id=current_user.id, symbol=symbol, action="BUY",
                 qty=trade.quantity, price=current_price, total=total_cost)
        return {"message": f"Bought {trade.quantity} shares of {symbol} at ${current_price:.2f}"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(TRADE_EXECUTED, user_id=current_user.id, symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail="Trade failed. Please try again.")


@router.post("/sell")
def sell_stock(trade: TradeAction, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if trade.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    symbol = trade.symbol.upper()
    current_price = _fetch_current_price(symbol)
    total_revenue = current_price * trade.quantity

    try:
        # IMPROVEMENT #2: Lock wallet row for atomic update
        from database import IS_SQLITE
        wallet_query = db.query(models.Wallet).filter(models.Wallet.user_id == current_user.id)
        if not IS_SQLITE:
            wallet_query = wallet_query.with_for_update()
            
        wallet = wallet_query.first()
        position = db.query(models.Position).filter(
            models.Position.user_id == current_user.id,
            models.Position.symbol == symbol
        ).first()

        if not position or position.quantity < trade.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient shares. Own {position.quantity if position else 0}, want to sell {trade.quantity}"
            )

        wallet.balance = float(wallet.balance) + total_revenue
        position.quantity -= trade.quantity
        if position.quantity == 0:
            db.delete(position)

        db.add(models.Transaction(
            user_id=current_user.id, symbol=symbol, action="SELL",
            quantity=trade.quantity, price=current_price,
            reason="Manual sell order"
        ))
        db.commit()

        log.info(TRADE_EXECUTED, user_id=current_user.id, symbol=symbol, action="SELL",
                 qty=trade.quantity, price=current_price, revenue=total_revenue)
        return {"message": f"Sold {trade.quantity} shares of {symbol} at ${current_price:.2f}"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(TRADE_EXECUTED, user_id=current_user.id, symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail="Trade failed. Please try again.")


@router.get("/logs")
def get_trade_logs(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all trade transactions for the current user from the DB (not in-memory)."""
    transactions = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.action.in_(["BUY", "SELL", "SKIP_BUY", "SKIP_SELL"])
        )
        .order_by(models.Transaction.timestamp.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "id": t.id,
            "timestamp": t.timestamp.isoformat(),
            "symbol": t.symbol,
            "action": t.action,
            "quantity": t.quantity,
            "price": float(t.price),
            "reason": t.reason or "",
        }
        for t in transactions
    ]
