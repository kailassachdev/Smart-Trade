"""
routers/agent.py
----------------
AI agent control endpoints: start, stop, simulate.

ARCHITECTURAL IMPROVEMENTS:
- #3: Uses APScheduler (scheduler.py) instead of raw threading.Thread
- #3: agent_enabled persisted to DB — survives server restarts
- #8: Structured logging
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
from database import get_db
from routers.auth import get_current_user
from scheduler import agent_scheduler
from logging_config import get_logger, AGENT_DECISION

log = get_logger("agent")
router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/start")
def start_agent(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # IMPROVEMENT #3: Persist state in DB so restarts don't stop the agent
    if not current_user.agent_enabled:
        current_user.agent_enabled = True
        db.commit()

    agent_scheduler.start_for_user(current_user.id)
    log.info(AGENT_DECISION, user_id=current_user.id, event="agent_start")

    if agent_scheduler.is_running_for_user(current_user.id):
        return {"status": "Agent started for your portfolio"}
    return {"status": "Agent already running for your portfolio"}


@router.post("/stop")
def stop_agent(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.agent_enabled = False
    db.commit()

    agent_scheduler.stop_for_user(current_user.id)
    log.info(AGENT_DECISION, user_id=current_user.id, event="agent_stop")
    return {"status": "Agent stopping for your portfolio"}


@router.post("/simulate")
def simulate_trade(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Immediately trigger one agent cycle for the current user (for testing)."""
    from main import execute_trade_logic
    log_entry = execute_trade_logic(current_user.id, db)
    return log_entry or {"status": "Simulation attempted but skipped (check balance or shares)"}
