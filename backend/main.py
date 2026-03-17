"""
main.py
-------
Smart Trade API — Production-grade refactor.

This file is now a THIN APPLICATION FACTORY.
All route logic has been extracted to routers/ sub-modules.
The agent's core trade execution logic lives here because routers/agent.py and
scheduler.py both import it, and placing it here avoids circular imports.

ARCHITECTURAL IMPROVEMENTS ASSEMBLED HERE:
  #1  — PostgreSQL-ready database (via database.py)
  #2  — Atomic transactions with SELECT FOR UPDATE (inside routers/)
  #3  — APScheduler agent (scheduler.py starts on FastAPI startup)
  #4  — Deterministic indicator layer (indicators.py) before LLM
  #5  — Risk management checks (risk.py) before every AI trade
  #6  — Per-user isolated scheduler jobs (scheduler.py)
  #7  — JWT expiry + HttpOnly cookie (routers/auth.py)
  #8  — Structured logging (logging_config.py)
  #9  — Market-hours awareness (market_hours.py) gates agent trades
  #10 — API split into router sub-modules (routers/)
"""

import os
import random
import uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import models
from database import engine, SessionLocal
from logging_config import configure_logging, get_logger, AGENT_DECISION, TRADE_EXECUTED, TRADE_SKIPPED, RISK_BLOCKED
from market_hours import is_market_open
from indicators import compute_signal
from risk import risk_manager
from ollama_service import OllamaService
import yfinance as yf

# ── Bootstrap ──────────────────────────────────────────────────────────────────
configure_logging()   # Must be first
log = get_logger("main")

models.Base.metadata.create_all(bind=engine)   # Creates tables if they don't exist

# ── Application factory ────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Trade API",
    description="Production-grade AI trading platform",
    version="2.0.0",
)

# CORS — restrict to specific origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request ID middleware (IMPROVEMENT #8: traceability) ──────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ── Mount routers ──────────────────────────────────────────────────────────────
from routers import auth, wallet, trade, portfolio, agent, market

app.include_router(auth.router)
app.include_router(wallet.router)
app.include_router(trade.router)
app.include_router(portfolio.router)
app.include_router(agent.router)
app.include_router(market.router)

# ── Legacy route aliases for frontend compatibility ───────────────────────────
# The React frontend uses /start-agent, /stop-agent, /trade-logs — keep these working
from fastapi import Depends
from routers.auth import get_current_user
from sqlalchemy.orm import Session
from database import get_db

@app.get("/")
def read_root():
    return {"status": "Smart Trade API v2.0 is running"}

@app.post("/start-agent")
def start_agent_compat(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from routers.agent import start_agent
    return start_agent(current_user=current_user, db=db)

@app.post("/stop-agent")
def stop_agent_compat(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from routers.agent import stop_agent
    return stop_agent(current_user=current_user, db=db)

@app.get("/trade-logs")
def trade_logs_compat(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    from routers.trade import get_trade_logs
    return get_trade_logs(current_user=current_user, db=db)

@app.post("/simulate-trade")
def simulate_trade_compat(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_entry = execute_trade_logic(current_user.id, db)
    return log_entry or {"status": "Simulation skipped (check balance or market hours)"}


# ── AI Agent Lifecycle (FastAPI startup / shutdown) ───────────────────────────
from scheduler import agent_scheduler

@app.on_event("startup")
def on_startup():
    # IMPROVEMENT #3: APScheduler manages agent lifecycle
    # restore_active_agents() is called separately after scheduler.start() to avoid
    # any circular import resolution during the FastAPI lifespan startup phase
    try:
        agent_scheduler.start()
        agent_scheduler.restore_active_agents()  # Re-activate agents that were running before restart
        log.info("app_startup", msg="Smart Trade API v2.0 started")
    except Exception as e:
        log.error("app_startup", error=str(e))
        # Don't crash the server if scheduler fails — app still works without agent

@app.on_event("shutdown")
def on_shutdown():
    try:
        agent_scheduler.stop()
    except Exception:
        pass
    log.info("app_shutdown", msg="Smart Trade API v2.0 stopped")


# ── AI Agent Core Trade Logic ─────────────────────────────────────────────────
TRADE_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "BTC-USD", "ETH-USD"]
ollama_svc = OllamaService(model=os.getenv("OLLAMA_MODEL", "deepseek-v3.1:671b-cloud"))


def execute_trade_logic(user_id: int, db: Session) -> dict | None:
    """
    FULLY REFACTORED AI agent trade execution.

    Pipeline (IMPROVEMENT #4 — Deterministic first, LLM second):
      1. Fetch market data from yfinance
      2. Compute RSI/MACD/SMA signal (indicators.py) — deterministic, no randomness
      3. If confidence < 0.5 → HOLD, skip LLM call entirely
      4. Run risk checks (risk.py) — position size, stop-loss, exposure cap
      5. If risk blocked → log RISK_BLOCKED, skip trade
      6. Call LLM (OllamaService) to generate human-readable reasoning (validator role only)
      7. Execute trade atomically with SELECT FOR UPDATE on wallet row
      8. Persist decision to Transaction table with full reason text (IMPROVEMENT #8)
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    symbol = random.choice(TRADE_SYMBOLS)

    # IMPROVEMENT #9: Gate equity trades on market hours
    if not is_market_open(symbol):
        log.info(TRADE_SKIPPED, user_id=user_id, symbol=symbol,
                 reason="Market closed — skipping equity trade")
        # Still log to DB so the frontend shows the skip
        _persist_skip(db, user_id, symbol, "SKIP_BUY", 0, 0.0,
                      "Market is currently closed for this symbol.")
        return _make_log(symbol, "SKIP_BUY", 0, 0.0, "Market is currently closed for this symbol.")

    # ── Step 1: Fetch real market data ────────────────────────────────────────
    try:
        ticker = yf.Ticker(symbol)
        df     = ticker.history(period="1mo", interval="1d")   # 1 month for indicator computation
        if df.empty:
            raise ValueError("Empty dataframe")
        current_price = float(df["Close"].iloc[-1])
        open_price    = float(df["Open"].iloc[-1])
        change_pct    = ((current_price - open_price) / open_price) * 100
    except Exception as e:
        log.error(TRADE_SKIPPED, user_id=user_id, symbol=symbol, error=str(e))
        return None

    # ── Step 2 & 3: Deterministic technical signal (IMPROVEMENT #4) ──────────
    signal = compute_signal(df, symbol=symbol)
    log.info(AGENT_DECISION, user_id=user_id, symbol=symbol,
             signal_action=signal.action, confidence=signal.confidence,
             reasoning=signal.reasoning)

    if signal.action == "HOLD" or signal.confidence < 0.5:
        reason = f"Technical indicators say HOLD (confidence {signal.confidence:.0%}). {signal.reasoning}"
        _persist_skip(db, user_id, symbol, "SKIP_BUY", 0, current_price, reason)
        return _make_log(symbol, "SKIP_BUY", 0, current_price, reason)

    action   = signal.action
    quantity = random.randint(1, 3)   # Smaller than before; risk.py will cap further

    # ── Step 4 & 5: Risk management checks (IMPROVEMENT #5) ──────────────────
    if action == "BUY":
        risk = risk_manager.validate_buy(user, symbol, quantity, current_price, db)
    else:
        position = db.query(models.Position).filter(
            models.Position.user_id == user_id,
            models.Position.symbol == symbol
        ).first()
        risk = risk_manager.validate_sell(position, current_price)
        # Handle stop-loss override
        if not risk.approved and risk.override_action:
            action   = risk.override_action
            quantity = position.quantity if position else 0

    if not risk.approved and not risk.override_action:
        log.warning(RISK_BLOCKED, user_id=user_id, symbol=symbol, action=action, reason=risk.reason)
        skip_action = f"SKIP_{action}"
        _persist_skip(db, user_id, symbol, skip_action, quantity, current_price, risk.reason)
        return _make_log(symbol, skip_action, quantity, current_price, risk.reason)

    # ── Step 6: LLM enriches with human-readable reasoning (validator only) ──
    market_context = {
        "symbol": symbol, "price": f"${current_price:.2f}",
        "daily_change": f"{change_pct:.2f}%",
        "technical_signal": signal.reasoning,
        "proposed_action": action,
    }
    llm_reason = ollama_svc.analyze_market(market_context)
    if "Error" in llm_reason:
        llm_reason = signal.reasoning   # Fall back to deterministic reasoning

    reason = f"[Indicators] {signal.reasoning} | [LLM] {llm_reason}"

    # ── Step 7: Execute trade atomically (IMPROVEMENT #2) ────────────────────
    try:
        from database import IS_SQLITE
        wallet_query = db.query(models.Wallet).filter(models.Wallet.user_id == user_id)
        if not IS_SQLITE:
            wallet_query = wallet_query.with_for_update()
            
        wallet = wallet_query.first()
        total_cost = current_price * quantity

        if action == "BUY":
            if not wallet or float(wallet.balance) < total_cost:
                skip_reason = (
                    f"Insufficient funds: need ${total_cost:.2f}, "
                    f"have ${float(wallet.balance) if wallet else 0:.2f}"
                )
                _persist_skip(db, user_id, symbol, "SKIP_BUY", quantity, current_price, skip_reason)
                return _make_log(symbol, "SKIP_BUY", quantity, current_price, skip_reason)

            wallet.balance = float(wallet.balance) - total_cost
            _update_position_buy(db, user_id, symbol, quantity, current_price)

        elif action == "SELL":
            position = db.query(models.Position).filter(
                models.Position.user_id == user_id,
                models.Position.symbol == symbol
            ).first()
            if not position or position.quantity < quantity:
                skip_reason = f"Insufficient shares: own {position.quantity if position else 0}, need {quantity}"
                _persist_skip(db, user_id, symbol, "SKIP_SELL", quantity, current_price, skip_reason)
                return _make_log(symbol, "SKIP_SELL", quantity, current_price, skip_reason)

            wallet.balance = float(wallet.balance) + total_cost
            position.quantity -= quantity
            if position.quantity == 0:
                db.delete(position)

        # ── Step 8: Persist trade with reason (IMPROVEMENT #8) ───────────────
        db.add(models.Transaction(
            user_id=user_id, symbol=symbol, action=action,
            quantity=quantity, price=current_price, reason=reason
        ))
        db.commit()

        log.info(TRADE_EXECUTED, user_id=user_id, symbol=symbol, action=action,
                 qty=quantity, price=current_price, reason=reason[:100])

    except Exception as e:
        db.rollback()
        log.error(TRADE_EXECUTED, user_id=user_id, symbol=symbol, error=str(e))
        return None

    return _make_log(symbol, action, quantity, current_price, reason)


# ── Private helpers ────────────────────────────────────────────────────────────
def _update_position_buy(db: Session, user_id: int, symbol: str, quantity: int, price: float):
    position = db.query(models.Position).filter(
        models.Position.user_id == user_id,
        models.Position.symbol == symbol
    ).first()
    if position:
        total_val              = (float(position.quantity) * float(position.average_price)) + (price * quantity)
        position.quantity     += quantity
        position.average_price = total_val / position.quantity
    else:
        db.add(models.Position(user_id=user_id, symbol=symbol, quantity=quantity, average_price=price))


def _persist_skip(db: Session, user_id: int, symbol: str, action: str, qty: int, price: float, reason: str):
    try:
        db.add(models.Transaction(
            user_id=user_id, symbol=symbol, action=action,
            quantity=qty, price=price if price > 0 else 0.0, reason=reason
        ))
        db.commit()
    except Exception:
        db.rollback()


def _make_log(symbol: str, action: str, qty: int, price: float, reason: str) -> dict:
    return {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol, "action": action,
        "quantity": qty, "price": price, "reason": reason,
    }
