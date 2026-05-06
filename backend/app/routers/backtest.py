"""Research / backtest endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services import backtest as bt

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.get("/summary")
def summary() -> dict:
    return {
        "summary": bt.load_summary(),
        "metadata": bt.load_metadata(),
    }


@router.get("/predictions")
def predictions() -> List[dict]:
    return bt.load_predictions()


@router.get("/calibration")
def calibration() -> List[dict]:
    return bt.load_calibration()


@router.get("/ablations")
def ablations() -> List[dict]:
    return bt.load_ablations()


class RunRequest(BaseModel):
    n_games: int = 25
    season: str = "2025-26"
    min_history: int = 10


@router.post("/run")
def run(req: RunRequest) -> dict:
    if req.n_games < 1 or req.n_games > 500:
        raise HTTPException(status_code=400, detail="n_games out of range")
    ok, output = bt.run_backtest(req.n_games, req.season, req.min_history)
    return {"ok": ok, "output": output[-6000:]}


@router.get("/simulate")
def simulate(
    method: str = "All",
    edge_threshold: float = Query(0.05, ge=0.0, le=0.5),
    side_filter: str = "Both",
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
) -> dict:
    return bt.simulate_roi(
        method=method,
        edge_threshold=edge_threshold,
        side_filter=side_filter,
        min_confidence=min_confidence,
    )
