"""
indicators.py
-------------
Deterministic technical indicator computation using pandas-ta.
This is the FIRST layer of the AI decision pipeline. The LLM only sees data
AFTER this module has produced a signal — preventing hallucinated trade directions.

ARCHITECTURAL IMPROVEMENT #4: Deterministic AI Decision Pipeline
"""

import pandas as pd
import pandas_ta as ta           # pip install pandas-ta
from dataclasses import dataclass
from typing import Literal


@dataclass
class TechnicalSignal:
    """Structured output from the indicator layer."""
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float          # 0.0 – 1.0
    reasoning: str             # Human-readable rationale fed into the LLM as context


def compute_signal(df: pd.DataFrame, symbol: str = "") -> TechnicalSignal:
    """
    Compute RSI, MACD, and SMA crossover signals from a OHLCV DataFrame.
    Returns a TechnicalSignal representing the composite view.

    Args:
        df:      yfinance history DataFrame (must have 'Close' column)
        symbol:  Ticker string for logging context

    Decision rules (deterministic — no randomness):
      BUY  if: RSI < 45  AND  MACD line crosses above signal line  AND  price > SMA(20)
      SELL if: RSI > 65  AND  MACD line crosses below signal line  AND  price < SMA(20)
      HOLD if: none of the above conditions are met simultaneously
    Confidence = proportion of bullish/bearish conditions satisfied (0.33 / 0.67 / 1.0)
    """
    if df is None or len(df) < 26:
        # Not enough data to compute MACD (requires at least 26 periods)
        return TechnicalSignal(
            action="HOLD",
            confidence=0.0,
            reasoning=f"Insufficient historical data for {symbol} to compute indicators."
        )

    close = df["Close"]

    # ── RSI (14-period) ───────────────────────────────────────────────────────
    rsi_series = ta.rsi(close, length=14)
    rsi = float(rsi_series.iloc[-1]) if rsi_series is not None and not rsi_series.empty else 50.0

    # ── MACD ──────────────────────────────────────────────────────────────────
    macd_df = ta.macd(close)           # Returns DataFrame with MACD, MACDh, MACDs columns
    if macd_df is not None and not macd_df.empty:
        macd_line   = float(macd_df["MACD_12_26_9"].iloc[-1])
        signal_line = float(macd_df["MACDs_12_26_9"].iloc[-1])
        macd_bullish = macd_line > signal_line   # MACD line above signal → bullish momentum
    else:
        macd_line, signal_line, macd_bullish = 0.0, 0.0, False

    # ── SMA Crossover (20-period) ─────────────────────────────────────────────
    sma_20 = ta.sma(close, length=20)
    current_price = float(close.iloc[-1])
    if sma_20 is not None and not sma_20.empty:
        sma_val = float(sma_20.iloc[-1])
        price_above_sma = current_price > sma_val
    else:
        sma_val = current_price
        price_above_sma = False

    # ── Composite Decision ────────────────────────────────────────────────────
    bullish_signals = sum([rsi < 45, macd_bullish, price_above_sma])
    bearish_signals = sum([rsi > 65, not macd_bullish, not price_above_sma])

    # Require at least 2/3 conditions to agree for a directional signal
    if bullish_signals >= 2:
        action = "BUY"
        confidence = bullish_signals / 3.0
    elif bearish_signals >= 2:
        action = "SELL"
        confidence = bearish_signals / 3.0
    else:
        action = "HOLD"
        confidence = 0.3   # Low conviction → don't trade

    reasoning = (
        f"[{symbol}] RSI={rsi:.1f}, MACD={'bullish' if macd_bullish else 'bearish'} "
        f"(line={macd_line:.3f} vs signal={signal_line:.3f}), "
        f"Price {'above' if price_above_sma else 'below'} SMA20={sma_val:.2f}. "
        f"Bullish signals: {bullish_signals}/3, Bearish: {bearish_signals}/3 → {action} "
        f"(confidence {confidence:.0%})"
    )

    return TechnicalSignal(action=action, confidence=confidence, reasoning=reasoning)
