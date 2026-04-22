"""
Step 3: NBA Odds Data Pipeline
Pulls betting odds from The Odds API (live) and Kaggle (historical).

Setup:
    1. Get a free API key from https://the-odds-api.com
    2. Set it as an environment variable: export ODDS_API_KEY="your_key_here"
    3. Download historical odds CSV from Kaggle:
       https://www.kaggle.com/datasets/erichqiu/nba-odds-and-scores
       Place it in data/kaggle_odds.csv (optional, for historical evaluation)

Usage:
    pip install requests pandas
    python nba_odds_pipeline.py

Output:
    data/odds_live.csv       - Current odds for upcoming games
    data/odds_historical.csv - Historical odds for evaluation (from Kaggle or API)
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# The Odds API config
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"


def pull_live_odds():
    """
    Pull current odds for upcoming NBA games from The Odds API.
    Uses 1 credit per call (moneyline, one region).
    """
    print("Pulling live odds from The Odds API...")

    if not ODDS_API_KEY:
        print("  No API key found. Set ODDS_API_KEY environment variable.")
        print("  Get a free key at https://the-odds-api.com")
        print("  Skipping live odds.")
        return pd.DataFrame()

    try:
        url = f"{ODDS_API_BASE}/sports/{SPORT}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            remaining = response.headers.get("x-requests-remaining", "?")
            used = response.headers.get("x-requests-used", "?")
            print(f"  API credits used: {used}, remaining: {remaining}")

            if not data:
                print("  No upcoming games found (NBA might be off-season).")
                return pd.DataFrame()

            # Flatten the nested JSON into rows
            rows = []
            for game in data:
                game_info = {
                    "GAME_ID": game["id"],
                    "SPORT": game["sport_key"],
                    "COMMENCE_TIME": game["commence_time"],
                    "HOME_TEAM": game["home_team"],
                    "AWAY_TEAM": game["away_team"],
                }

                for bookmaker in game.get("bookmakers", []):
                    for market in bookmaker.get("markets", []):
                        for outcome in market.get("outcomes", []):
                            row = {
                                **game_info,
                                "BOOKMAKER": bookmaker["key"],
                                "MARKET": market["key"],
                                "OUTCOME_NAME": outcome["name"],
                                "PRICE": outcome.get("price"),
                                "POINT": outcome.get("point"),
                                "LAST_UPDATE": bookmaker.get("last_update"),
                            }
                            rows.append(row)

            df = pd.DataFrame(rows)
            print(f"  Pulled odds for {len(data)} upcoming games ({len(rows)} odds entries)")
            return df

        elif response.status_code == 401:
            print("  Invalid API key. Check your ODDS_API_KEY.")
            return pd.DataFrame()
        elif response.status_code == 429:
            print("  Rate limited. Wait and try again.")
            return pd.DataFrame()
        else:
            print(f"  API error: {response.status_code}")
            return pd.DataFrame()

    except Exception as e:
        print(f"  Error: {e}")
        return pd.DataFrame()


def load_kaggle_historical_odds():
    """
    Load historical odds from a Kaggle dataset.
    User needs to download the CSV manually and place it in data/kaggle_odds.csv.

    Recommended dataset:
    https://www.kaggle.com/datasets/erichqiu/nba-odds-and-scores
    """
    print("Loading historical odds from Kaggle...")

    kaggle_path = f"{DATA_DIR}/kaggle_odds.csv"
    if os.path.exists(kaggle_path):
        df = pd.read_csv(kaggle_path)
        print(f"  Loaded {len(df)} rows from {kaggle_path}")
        return df
    else:
        print(f"  No file found at {kaggle_path}")
        print("  To get historical odds for evaluation:")
        print("    1. Go to https://www.kaggle.com/datasets/erichqiu/nba-odds-and-scores")
        print("    2. Download the CSV")
        print(f"    3. Save it as {kaggle_path}")
        print("  Skipping historical odds for now.")
        return pd.DataFrame()


def compute_implied_probability(american_odds):
    """Convert American odds to implied probability."""
    try:
        odds = float(american_odds)
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return abs(odds) / (abs(odds) + 100)
    except (ValueError, TypeError):
        return None


def enrich_odds_data(df):
    """Add implied probabilities and identify best odds across bookmakers."""
    if df.empty:
        return df

    print("Enriching odds data with implied probabilities...")

    # Add implied probability
    if "PRICE" in df.columns:
        df["IMPLIED_PROB"] = df["PRICE"].apply(compute_implied_probability)

    # For moneyline (h2h), find best odds per team per game
    h2h = df[df["MARKET"] == "h2h"].copy() if "MARKET" in df.columns else df.copy()
    if not h2h.empty and "GAME_ID" in h2h.columns:
        best_odds = (
            h2h.groupby(["GAME_ID", "OUTCOME_NAME"])
            .agg(
                BEST_PRICE=("PRICE", "max"),
                WORST_PRICE=("PRICE", "min"),
                NUM_BOOKMAKERS=("BOOKMAKER", "nunique"),
            )
            .reset_index()
        )
        best_odds.to_csv(f"{DATA_DIR}/odds_best_lines.csv", index=False)
        print(f"  Saved best lines to {DATA_DIR}/odds_best_lines.csv")

    return df


def main():
    print("=" * 60)
    print("NBA Odds Pipeline - Step 3")
    print("=" * 60)
    
    live_path = f"{DATA_DIR}/odds_live.csv"
    if os.path.exists(live_path):
        os.remove(live_path)

    # 1. Pull live odds (for demo)
    live_odds = pull_live_odds()
    if not live_odds.empty:
        live_odds = enrich_odds_data(live_odds)
        live_odds.to_csv(f"{DATA_DIR}/odds_live.csv", index=False)
        print(f"Saved live odds to {DATA_DIR}/odds_live.csv")
    print()

    # 2. Load historical odds (for evaluation)
    historical = load_kaggle_historical_odds()
    if not historical.empty:
        historical.to_csv(f"{DATA_DIR}/odds_historical.csv", index=False)
        print(f"Saved historical odds to {DATA_DIR}/odds_historical.csv")
    print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Live odds entries: {len(live_odds)}")
    print(f"Historical odds entries: {len(historical)}")
    if not live_odds.empty:
        print(f"Upcoming games: {live_odds['GAME_ID'].nunique() if 'GAME_ID' in live_odds.columns else 'N/A'}")
        print(f"Bookmakers: {live_odds['BOOKMAKER'].nunique() if 'BOOKMAKER' in live_odds.columns else 'N/A'}")
    print()
    print("Next: Run step 4 (Reddit sentiment pipeline)")


if __name__ == "__main__":
    main()
