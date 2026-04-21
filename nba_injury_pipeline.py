"""
Step 2: NBA Injury Data Pipeline
Scrapes current injury data from ESPN's NBA injury page.

ESPN table columns: NAME | POS | EST. RETURN DATE | STATUS | COMMENT

Usage:
    pip install requests beautifulsoup4 pandas
    python nba_injury_pipeline.py

Output:
    data/injuries.csv - Current NBA injury reports
"""

import os
import requests
import pandas as pd
from datetime import datetime

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

ESPN_INJURY_URL = "https://www.espn.com/nba/injuries"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def scrape_espn_injuries():
    """
    Scrape current NBA injury data from ESPN.
    ESPN columns: NAME, POS, EST. RETURN DATE, STATUS, COMMENT
    """
    print("Scraping NBA injuries from ESPN...")

    try:
        from bs4 import BeautifulSoup

        response = requests.get(ESPN_INJURY_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        rows = []

        tables = soup.find_all("table")
        if not tables:
            print("  No tables found on ESPN page.")
            return pd.DataFrame()

        current_team = "Unknown"

        for table in tables:
            # Find team name: look for the nearest preceding image alt text or heading
            # ESPN uses team logo images with alt text = team name
            prev_elements = table.find_all_previous(["img", "h2", "h3", "span"], limit=10)
            for el in prev_elements:
                if el.name == "img" and el.get("title"):
                    current_team = el["title"]
                    break
                elif el.name == "img" and el.get("alt") and len(el["alt"]) > 3 and "logo" not in el["alt"].lower():
                    current_team = el["alt"]
                    break

            for tr in table.find_all("tr"):
                cells = tr.find_all(["td", "th"])
                texts = [c.get_text(strip=True) for c in cells]

                # Skip header rows (NAME, POS, etc.)
                if not texts or texts[0].upper() in ["NAME", "PLAYER", ""]:
                    continue

                # ESPN format: NAME | POS | EST. RETURN DATE | STATUS | COMMENT
                if len(texts) >= 4:
                    row = {
                        "TEAM": current_team,
                        "PLAYER_NAME": texts[0],
                        "POSITION": texts[1] if len(texts) > 1 else "",
                        "EST_RETURN": texts[2] if len(texts) > 2 else "",
                        "STATUS": texts[3] if len(texts) > 3 else "",
                        "COMMENT": texts[4] if len(texts) > 4 else "",
                        "SCRAPE_DATE": datetime.now().strftime("%Y-%m-%d"),
                    }
                    rows.append(row)

        if rows:
            df = pd.DataFrame(rows)
            print(f"  Scraped {len(df)} injury entries across {df['TEAM'].nunique()} teams")
            return df
        else:
            print("  No injury data parsed.")
            return pd.DataFrame()

    except ImportError:
        print("  beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        return pd.DataFrame()
    except requests.RequestException as e:
        print(f"  Request failed: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"  Error: {e}")
        return pd.DataFrame()


def main():
    print("=" * 60)
    print("NBA Injury Pipeline - Step 2")
    print("=" * 60)

    injuries = scrape_espn_injuries()

    if injuries.empty:
        print("  No data scraped. Creating empty schema.")
        injuries = pd.DataFrame(columns=[
            "TEAM", "PLAYER_NAME", "POSITION", "EST_RETURN",
            "STATUS", "COMMENT", "SCRAPE_DATE"
        ])

    injuries.to_csv(f"{DATA_DIR}/injuries.csv", index=False)

    print()
    print(f"Saved to {DATA_DIR}/injuries.csv")
    print(f"Total records: {len(injuries)}")
    if len(injuries) > 0 and "STATUS" in injuries.columns:
        print(f"Status breakdown: {injuries['STATUS'].value_counts().to_dict()}")
        print(f"Teams: {injuries['TEAM'].nunique()}")
        print()
        print("Sample entries:")
        for _, row in injuries.head(3).iterrows():
            print(f"  {row['TEAM']} - {row['PLAYER_NAME']} ({row['POSITION']}) - {row['STATUS']} - {row['COMMENT'][:80]}...")
    print()
    print("Next: Run step 3 (odds pipeline)")


if __name__ == "__main__":
    main()