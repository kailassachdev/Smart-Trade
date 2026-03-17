"""
routers/wallet.py
-----------------
Wallet management endpoints: deposit, withdraw, history.

ARCHITECTURAL IMPROVEMENTS:
- #2: SELECT FOR UPDATE lock on wallet row to prevent concurrent modification
- #8: Structured logging for every wallet update
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
from database import get_db
from routers.auth import get_current_user
from logging_config import get_logger, WALLET_UPDATE

log = get_logger("wallet")
router = APIRouter(prefix="/wallet", tags=["wallet"])


class WalletAction(BaseModel):
    amount: float


@router.post("/deposit")
def deposit(action: WalletAction, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if action.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    try:
        # IMPROVEMENT #2: Lock the wallet row to prevent concurrent deposits/withdrawals (PostgreSQL only)
        from database import IS_SQLITE
        wallet_query = db.query(models.Wallet).filter(models.Wallet.user_id == current_user.id)
        if not IS_SQLITE:
            wallet_query = wallet_query.with_for_update()
        
        wallet = wallet_query.first()
        if not wallet:
            wallet = models.Wallet(user_id=current_user.id, balance=action.amount)
            db.add(wallet)
        else:
            wallet.balance = float(wallet.balance) + action.amount

        db.add(models.Transaction(
            user_id=current_user.id, symbol="USD",
            action="DEPOSIT", quantity=1, price=action.amount,
            reason="Manual deposit"
        ))
        db.commit()
        db.refresh(wallet)

        log.info(WALLET_UPDATE, user_id=current_user.id, action="DEPOSIT",
                 amount=action.amount, new_balance=float(wallet.balance))
        return {"message": "Deposit successful", "new_balance": float(wallet.balance)}

    except Exception as e:
        db.rollback()
        log.error(WALLET_UPDATE, user_id=current_user.id, action="DEPOSIT", error=str(e))
        raise HTTPException(status_code=500, detail="Deposit failed. Please try again.")


@router.post("/withdraw")
def withdraw(action: WalletAction, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if action.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    try:
        # IMPROVEMENT #2: Lock wallet row before reading balance
        from database import IS_SQLITE
        wallet_query = db.query(models.Wallet).filter(models.Wallet.user_id == current_user.id)
        if not IS_SQLITE:
            wallet_query = wallet_query.with_for_update()
            
        wallet = wallet_query.first()
        if not wallet or float(wallet.balance) < action.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        wallet.balance = float(wallet.balance) - action.amount

        db.add(models.Transaction(
            user_id=current_user.id, symbol="USD",
            action="WITHDRAW", quantity=1, price=action.amount,
            reason="Manual withdrawal"
        ))
        db.commit()
        db.refresh(wallet)

        log.info(WALLET_UPDATE, user_id=current_user.id, action="WITHDRAW",
                 amount=action.amount, new_balance=float(wallet.balance))
        return {"message": "Withdrawal successful", "new_balance": float(wallet.balance)}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        log.error(WALLET_UPDATE, user_id=current_user.id, action="WITHDRAW", error=str(e))
        raise HTTPException(status_code=500, detail="Withdrawal failed. Please try again.")


@router.get("/history")
def get_wallet_history(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    transactions = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.action.in_(["DEPOSIT", "WITHDRAW"])
        )
        .order_by(models.Transaction.timestamp.desc())
        .all()
    )
    return [
        {
            "id": t.id,
            "action": t.action,
            "amount": float(t.price),
            "timestamp": t.timestamp.isoformat()
        }
        for t in transactions
    ]
