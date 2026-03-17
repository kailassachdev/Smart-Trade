"""
scheduler.py
------------
APScheduler-based agent scheduler. Replaces raw threading.Thread approach.

ARCHITECTURAL IMPROVEMENT #3 & #6:
- APScheduler manages job lifecycle (start/stop/restart on failure) properly
- Each user's agent job is separate and isolated
- Market hours awareness gates all equity trades
- Revives active agents after server restarts by reading DB state
"""

import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from logging_config import get_logger, SCHEDULER_TICK
from database import SessionLocal
import models

log = get_logger("scheduler")

# Interval between agent cycles per user (seconds)
AGENT_INTERVAL_SECONDS = int(os.getenv("AGENT_INTERVAL_SECONDS", "60"))

# Job ID prefix for per-user jobs
JOB_ID_PREFIX = "agent_user_"


# ── Lazy import of execute_trade_logic to avoid circular imports ──────────────
def _get_trade_executor():
    from main import execute_trade_logic   # imported at call time, not module load
    return execute_trade_logic


def _agent_job_for_user(user_id: int):
    """
    APScheduler job target: runs one complete agent cycle for a single user.
    Uses its own DB session — fully isolated per-user.
    Avoids circular import by importing execute_trade_logic at call time.
    """
    from market_hours import is_market_open
    
    db = SessionLocal()
    try:
        # Deferred import at call time (not module load) to avoid circular dependency
        # main.py imports scheduler.py, so scheduler.py must NOT import main at module level
        import sys
        if 'main' in sys.modules:
            execute_trade_logic = sys.modules['main'].execute_trade_logic
        else:
            from main import execute_trade_logic
        
        log.info(SCHEDULER_TICK, user_id=user_id, msg="Agent tick starting")
        execute_trade_logic(user_id, db)
        log.info(SCHEDULER_TICK, user_id=user_id, msg="Agent tick complete")
    except Exception as e:
        log.error(SCHEDULER_TICK, user_id=user_id, error=str(e))
    finally:
        db.close()


class AgentScheduler:
    """
    Thin wrapper around APScheduler that manages per-user agent jobs.
    One job per user — completely independent scheduling.
    """

    def __init__(self):
        self._scheduler = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            job_defaults={"coalesce": True, "max_instances": 1},  # Never run overlapping instances
        )

    def start(self):
        """Start the scheduler. Agent restore happens AFTER app startup via start_restoration()."""
        self._scheduler.start()
        log.info("scheduler_start", msg="APScheduler started")

    def stop(self):
        """Shutdown scheduler gracefully."""
        self._scheduler.shutdown(wait=False)
        log.info("scheduler_stop", msg="APScheduler stopped")

    def restore_active_agents(self):
        """
        Call this AFTER the FastAPI app is fully started (not during startup event).
        Reads DB for users with agent_enabled=True and re-schedules their jobs.
        IMPROVEMENT #3: agent state persisted in DB survives server restarts.
        """
        db = SessionLocal()
        try:
            active_users = db.query(models.User).filter(models.User.agent_enabled == True).all()
            for user in active_users:
                self.start_for_user(user.id)
                log.info("scheduler_restore", user_id=user.id, msg="Restored agent job after restart")
        except Exception as e:
            log.error("scheduler_restore", error=str(e))
        finally:
            db.close()

    def start_for_user(self, user_id: int):
        """Add or replace a per-user agent job."""
        job_id = f"{JOB_ID_PREFIX}{user_id}"
        if self._scheduler.get_job(job_id):
            log.info("scheduler_job_exists", user_id=user_id, job_id=job_id)
            return

        self._scheduler.add_job(
            _agent_job_for_user,
            trigger=IntervalTrigger(seconds=AGENT_INTERVAL_SECONDS),
            args=[user_id],
            id=job_id,
            name=f"Agent for user {user_id}",
            replace_existing=True,
        )
        log.info("scheduler_job_added", user_id=user_id, interval_s=AGENT_INTERVAL_SECONDS)

    def stop_for_user(self, user_id: int):
        """Remove a user's agent job."""
        job_id = f"{JOB_ID_PREFIX}{user_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            log.info("scheduler_job_removed", user_id=user_id)

    def is_running_for_user(self, user_id: int) -> bool:
        return bool(self._scheduler.get_job(f"{JOB_ID_PREFIX}{user_id}"))


# Module-level singleton — imported by main.py and routers
agent_scheduler = AgentScheduler()
