"""
risk.py
-------
Risk management engine. Called BEFORE every trade (both manual and AI agent)
to enforce portfolio-level safety rules.

ARCHITECTURAL IMPROVEMENT #5: Risk Management Rules
"""

from dataclasses import dataclass
from sqlalchemy.orm import Session
import models


# ── Configurable defaults (can be overridden per-user in the future) ──────────
DEFAULT_MAX_SINGLE_POSITION_PCT = 0.20   # No single stock > 20% of total portfolio
DEFAULT_STOP_LOSS_PCT           = 0.05   # Auto-sell if position drops 5% below avg entry
DEFAULT_MAX_SYMBOLS             = 10     # Max distinct holdings before new BUYs are blocked


@dataclass
class RiskDecision:
    """Outcome of a risk check."""
    approved: bool
    reason: str
    override_action: str | None = None  # e.g. "SELL" for stop-loss trigger


class RiskManager:
    """
    Stateless risk manager. All methods take a DB session and return a RiskDecision.
    No trade should be committed without passing through these checks first.
    """

    def __init__(
        self,
        max_position_pct: float = DEFAULT_MAX_SINGLE_POSITION_PCT,
        stop_loss_pct:    float = DEFAULT_STOP_LOSS_PCT,
        max_symbols:      int   = DEFAULT_MAX_SYMBOLS,
    ):
        self.max_position_pct = max_position_pct
        self.stop_loss_pct    = stop_loss_pct
        self.max_symbols      = max_symbols

    # ── 1. Position size limit ────────────────────────────────────────────────
    def check_position_size(
        self,
        user: models.User,
        symbol: str,
        new_quantity: int,
        current_price: float,
        db: Session,
    ) -> RiskDecision:
        """
        Refuse a BUY if it would make a single symbol exceed max_position_pct
        of the user's total portfolio value (cash + equity).
        """
        wallet_balance = user.wallet.balance if user.wallet else 0.0
        positions      = db.query(models.Position).filter(models.Position.user_id == user.id).all()

        total_equity = sum(p.quantity * p.average_price for p in positions)
        total_value  = wallet_balance + total_equity

        if total_value <= 0:
            # No portfolio yet; allow the first trade
            return RiskDecision(approved=True, reason="First trade — no portfolio baseline.")

        # Find existing quantity for this symbol
        existing = next((p for p in positions if p.symbol == symbol), None)
        existing_qty = existing.quantity if existing else 0

        new_total_units  = existing_qty + new_quantity
        new_position_val = new_total_units * current_price
        allocation_pct   = new_position_val / total_value

        if allocation_pct > self.max_position_pct:
            return RiskDecision(
                approved=False,
                reason=(
                    f"RISK: {symbol} would represent {allocation_pct:.1%} of portfolio "
                    f"(limit: {self.max_position_pct:.0%}). Trade blocked."
                )
            )
        return RiskDecision(approved=True, reason=f"{symbol} allocation OK ({allocation_pct:.1%}).")

    # ── 2. Stop-loss check ────────────────────────────────────────────────────
    def check_stop_loss(
        self,
        position: models.Position,
        current_price: float,
    ) -> RiskDecision:
        """
        Returns an override SELL decision if the current price has dropped
        more than stop_loss_pct below the position's average entry price.
        """
        if position is None or position.quantity == 0:
            return RiskDecision(approved=True, reason="No position to check stop-loss for.")

        drop_pct = (position.average_price - current_price) / position.average_price

        if drop_pct >= self.stop_loss_pct:
            return RiskDecision(
                approved=False,
                override_action="SELL",
                reason=(
                    f"STOP-LOSS triggered for {position.symbol}: "
                    f"current ${current_price:.2f} is {drop_pct:.1%} below avg entry "
                    f"${position.average_price:.2f} (threshold: {self.stop_loss_pct:.0%})."
                )
            )
        return RiskDecision(approved=True, reason=f"Stop-loss OK for {position.symbol}.")

    # ── 3. Max symbol / diversification cap ──────────────────────────────────
    def check_max_symbols(
        self,
        user: models.User,
        symbol: str,
        db: Session,
    ) -> RiskDecision:
        """
        Block new BUY orders if the user already holds the maximum number of
        distinct symbols (prevents over-concentration via quantity, not just %).
        """
        positions = db.query(models.Position).filter(models.Position.user_id == user.id).all()
        existing_symbols = {p.symbol for p in positions}

        # If this symbol is already held, adding to it is fine
        if symbol in existing_symbols:
            return RiskDecision(approved=True, reason=f"{symbol} already in portfolio — adding to position.")

        if len(existing_symbols) >= self.max_symbols:
            return RiskDecision(
                approved=False,
                reason=(
                    f"RISK: Portfolio already holds {len(existing_symbols)} distinct symbols "
                    f"(limit: {self.max_symbols}). Cannot open new position in {symbol}."
                )
            )
        return RiskDecision(approved=True, reason=f"Symbol cap OK ({len(existing_symbols)}/{self.max_symbols}).")

    # ── Convenience: run all BUY checks at once ───────────────────────────────
    def validate_buy(
        self,
        user: models.User,
        symbol: str,
        quantity: int,
        price: float,
        db: Session,
    ) -> RiskDecision:
        for check in [
            self.check_position_size(user, symbol, quantity, price, db),
            self.check_max_symbols(user, symbol, db),
        ]:
            if not check.approved:
                return check
        return RiskDecision(approved=True, reason="All risk checks passed.")

    # ── Convenience: run all SELL checks at once ──────────────────────────────
    def validate_sell(
        self,
        position: models.Position | None,
        current_price: float,
    ) -> RiskDecision:
        if position is None:
            return RiskDecision(approved=False, reason="No position found to sell.")
        return self.check_stop_loss(position, current_price)


# Module-level singleton to use throughout the application
risk_manager = RiskManager()
