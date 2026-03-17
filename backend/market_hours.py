"""
market_hours.py
---------------
Market hours awareness so the AI agent respects NYSE trading hours.
Crypto symbols (BTC-USD, ETH-USD, etc.) are exempt — they trade 24/7.

ARCHITECTURAL IMPROVEMENT #9: Market Hours Awareness
"""

from datetime import datetime, time, timedelta
import pytz

# US Eastern timezone (NYSE)
ET = pytz.timezone("America/New_York")

# NYSE regular session: Mon–Fri, 09:30–16:00 ET
MARKET_OPEN  = time(9, 30)
MARKET_CLOSE = time(16, 0)

# Symbols that trade 24/7 (no market-hours gate)
CRYPTO_SUFFIXES = ("-USD", "-BTC", "-ETH", "BTC", "ETH", "USDT")


def is_crypto(symbol: str) -> bool:
    """Return True if the symbol is a crypto asset that trades 24/7."""
    return any(symbol.upper().endswith(sfx) or symbol.upper().startswith(sfx)
               for sfx in CRYPTO_SUFFIXES)


def is_market_open(symbol: str | None = None) -> bool:
    """
    Return True if the NYSE is currently open.
    Crypto symbols always return True (24/7 market).
    """
    if symbol and is_crypto(symbol):
        return True   # Crypto trades around the clock

    now_et = datetime.now(ET)

    # Weekday check: Monday=0, Friday=4
    if now_et.weekday() > 4:
        return False

    current_time = now_et.time()
    return MARKET_OPEN <= current_time < MARKET_CLOSE


def time_until_next_open() -> timedelta:
    """
    Returns the timedelta until the next NYSE open.
    Useful for logging how long the agent will sleep.
    """
    now_et = datetime.now(ET)
    today_open = ET.localize(datetime(now_et.year, now_et.month, now_et.day,
                                       MARKET_OPEN.hour, MARKET_OPEN.minute))

    if now_et < today_open and now_et.weekday() <= 4:
        return today_open - now_et

    # Find next weekday
    days_ahead = 1
    while True:
        candidate = today_open + timedelta(days=days_ahead)
        if candidate.weekday() <= 4:   # Mon–Fri
            return candidate - now_et
        days_ahead += 1


def market_status_payload() -> dict:
    """Returns a dict suitable for the /market/status API endpoint."""
    open_ = is_market_open()
    return {
        "is_open": open_,
        "opens_at": None if open_ else (
            (datetime.now(ET) + time_until_next_open()).isoformat()
        ),
        "current_et_time": datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S %Z"),
    }
