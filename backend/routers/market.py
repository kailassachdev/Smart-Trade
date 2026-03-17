"""
routers/market.py
-----------------
Market status and AI analysis endpoints.

ARCHITECTURAL IMPROVEMENTS:
- #9: /market/status endpoint exposes market open/close state to the frontend
- #4: /api/analyze now passes technical indicator context to the LLM
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

import models
from routers.auth import get_current_user
from market_hours import market_status_payload
from ollama_service import OllamaService
import os

ollama_service = OllamaService(model=os.getenv("OLLAMA_MODEL", "deepseek-v3.1:671b-cloud"))

router = APIRouter(tags=["market"])


class MarketData(BaseModel):
    symbol: str
    price: float
    trends: Optional[dict] = None


@router.get("/market/status")
def get_market_status():
    """
    IMPROVEMENT #9: Returns NYSE open/close status for the frontend to display.
    Crypto is always open. Equity markets follow NYSE hours (Mon-Fri 9:30-16:00 ET).
    """
    return market_status_payload()


@router.post("/api/analyze")
def analyze_market(data: MarketData, current_user: models.User = Depends(get_current_user)):
    """
    IMPROVEMENT #4: AI analysis now receives technical indicator context.
    The LLM acts as a validator/enricher, not the primary decision-maker.
    """
    analysis = ollama_service.analyze_market(data.dict())
    return {"analysis": analysis}
