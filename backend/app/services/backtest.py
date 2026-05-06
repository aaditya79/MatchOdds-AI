"""Backtest CSV loaders + ROI simulator.

Reads the artifacts produced by ``nba_backtest.py``:
    data/backtest_summary.csv
    data/backtest_predictions.csv
    data/backtest_calibration.csv
    data/backtest_run_metadata.json
    data/backtest_ablation_*_summary.csv

Also runs ``nba_backtest.py`` as a subprocess on demand from the API.
"""

from __future__ import annotations

import glob
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import app.config  # noqa: F401 — path bootstrap
from app.config import DATA_DIR, REPO_ROOT


SUMMARY_PATH = DATA_DIR / "backtest_summary.csv"
PRED_PATH = DATA_DIR / "backtest_predictions.csv"
CAL_PATH = DATA_DIR / "backtest_calibration.csv"
META_PATH = DATA_DIR / "backtest_run_metadata.json"


METHOD_DISPLAY = {
    "single_agent": "Single Agent",
    "chain_of_thought": "Chain-of-Thought",
    "multi_agent_debate": "Multi-Agent Debate",
}


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Pandas -> JSON-safe list[dict] (drops NaN, stringifies datetimes)."""
    if df.empty:
        return []
    cleaned = df.copy()
    for col in cleaned.columns:
        if pd.api.types.is_datetime64_any_dtype(cleaned[col]):
            cleaned[col] = cleaned[col].astype(str)
    records = cleaned.where(pd.notnull(cleaned), None).to_dict(orient="records")
    # numpy scalars -> python primitives for JSON
    for rec in records:
        for k, v in list(rec.items()):
            if isinstance(v, (np.integer,)):
                rec[k] = int(v)
            elif isinstance(v, (np.floating,)):
                rec[k] = None if math.isnan(float(v)) else float(v)
            elif isinstance(v, (np.bool_,)):
                rec[k] = bool(v)
    return records


def load_summary() -> list[dict]:
    if not SUMMARY_PATH.exists():
        return []
    return _df_to_records(pd.read_csv(SUMMARY_PATH))


def load_predictions() -> list[dict]:
    if not PRED_PATH.exists():
        return []
    return _df_to_records(pd.read_csv(PRED_PATH))


def load_calibration() -> list[dict]:
    if not CAL_PATH.exists():
        return []
    return _df_to_records(pd.read_csv(CAL_PATH))


def load_metadata() -> dict:
    if not META_PATH.exists():
        return {}
    try:
        return json.loads(META_PATH.read_text())
    except Exception:
        return {}


def load_ablations() -> list[dict]:
    files = glob.glob(str(DATA_DIR / "backtest_ablation_*_summary.csv"))
    if not files or not SUMMARY_PATH.exists():
        return []
    base_df = pd.read_csv(SUMMARY_PATH)
    base_cot = base_df[base_df["method"] == "chain_of_thought"]
    if base_cot.empty:
        return []
    baseline_brier = float(base_cot["brier_score"].iloc[0])

    rows: list[dict] = []
    for fpath in sorted(files):
        path = Path(fpath)
        source = path.name.replace("backtest_ablation_", "").replace("_summary.csv", "")
        df = pd.read_csv(path)
        cot_row = df[df["method"] == "chain_of_thought"]
        if cot_row.empty:
            continue
        ablation_brier = float(cot_row["brier_score"].iloc[0])
        rows.append({
            "source": source,
            "ablation_brier": round(ablation_brier, 4),
            "baseline_brier": round(baseline_brier, 4),
            "brier_delta": round(ablation_brier - baseline_brier, 4),
            "n_games": int(cot_row["n_games"].iloc[0]),
        })
    rows.sort(key=lambda r: r["brier_delta"], reverse=True)
    return rows


# ---------------------------------------------------------------------------
# ROI simulator
# ---------------------------------------------------------------------------

def _safe_prob(value) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return min(max(x, 1e-6), 1 - 1e-6)


def simulate_roi(
    method: str = "All",
    edge_threshold: float = 0.05,
    side_filter: str = "Both",
    min_confidence: float = 0.50,
) -> dict:
    if not PRED_PATH.exists():
        return {"summary": [], "bets": [], "available": False}

    df = pd.read_csv(PRED_PATH)
    if df.empty or "market_home_implied_prob" not in df.columns or "market_away_implied_prob" not in df.columns:
        return {"summary": [], "bets": [], "available": False}

    if method != "All":
        df = df[df["method"] == method].copy()
    if df.empty:
        return {"summary": [], "bets": [], "available": True}

    sim_rows: list[dict] = []
    for _, row in df.iterrows():
        home_prob = _safe_prob(row.get("home_win_prob"))
        away_prob = _safe_prob(row.get("away_win_prob"))
        market_home = _safe_prob(row.get("market_home_implied_prob"))
        market_away = _safe_prob(row.get("market_away_implied_prob"))
        if any(math.isnan(x) for x in [home_prob, away_prob, market_home, market_away]):
            continue
        confidence = max(home_prob, away_prob)
        if confidence < min_confidence:
            continue

        home_edge = home_prob - market_home
        away_edge = away_prob - market_away
        chosen_side = chosen_edge = chosen_market_prob = None
        won = None

        if side_filter in ("Both", "Home Only") and home_edge >= edge_threshold:
            chosen_side = "Home"
            chosen_edge = home_edge
            chosen_market_prob = market_home
            won = int(row["actual_home_win"]) == 1
        if side_filter in ("Both", "Away Only") and away_edge >= edge_threshold:
            if chosen_side is None or away_edge > chosen_edge:
                chosen_side = "Away"
                chosen_edge = away_edge
                chosen_market_prob = market_away
                won = int(row["actual_home_win"]) == 0

        if chosen_side is None:
            continue

        decimal_odds = 1.0 / chosen_market_prob
        units = (decimal_odds - 1.0) if won else -1.0

        sim_rows.append({
            "date": str(row.get("date")),
            "season": row.get("season", ""),
            "game_id": row.get("game_id", ""),
            "away_team": row.get("away_team"),
            "home_team": row.get("home_team"),
            "method": row.get("method"),
            "side_bet": chosen_side,
            "edge": round(float(chosen_edge), 4),
            "model_home_prob": round(float(home_prob), 4),
            "model_away_prob": round(float(away_prob), 4),
            "market_home_implied_prob": round(float(market_home), 4),
            "market_away_implied_prob": round(float(market_away), 4),
            "model_confidence": round(float(confidence), 4),
            "won": int(bool(won)),
            "units": round(float(units), 4),
        })

    if not sim_rows:
        return {"summary": [], "bets": [], "available": True}

    bets_df = pd.DataFrame(sim_rows)
    bets_df["date"] = pd.to_datetime(bets_df["date"], errors="coerce")
    bets_df = bets_df.sort_values(["method", "date", "game_id"]).reset_index(drop=True)
    bets_df["cum_units"] = bets_df.groupby("method")["units"].cumsum()
    bets_df["date"] = bets_df["date"].astype(str)

    summary_df = (
        bets_df.groupby("method")
        .agg(
            n_bets=("units", "count"),
            win_rate=("won", "mean"),
            total_units=("units", "sum"),
            avg_units_per_bet=("units", "mean"),
            avg_edge=("edge", "mean"),
            avg_model_confidence=("model_confidence", "mean"),
        )
        .reset_index()
    )
    summary_df["roi"] = summary_df["total_units"] / summary_df["n_bets"]

    return {
        "summary": _df_to_records(summary_df),
        "bets": _df_to_records(bets_df),
        "available": True,
    }


def run_backtest(n_games: int, season: str, min_history: int) -> tuple[bool, str]:
    """Spawn ``nba_backtest.py`` and return (ok, combined_output)."""
    cmd = [
        sys.executable,
        "nba_backtest.py",
        "--n-games", str(n_games),
        "--min-games-history", str(min_history),
    ]
    if season and season != "All":
        cmd.extend(["--season", season])

    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")
