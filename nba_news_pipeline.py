"""
Step 5: NBA News Pipeline (Fixed)
Pulls NBA news from multiple sources with fallbacks.

Usage:
    pip install requests beautifulsoup4 feedparser pandas
    python nba_news_pipeline.py

Output:
    data/news_articles.csv - Recent NBA news articles
"""

import os
import re
import requests
import pandas as pd
from datetime import datetime

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Team keywords for tagging articles
TEAM_KEYWORDS = {
    "ATL": ["hawks", "atlanta hawks", "trae young"],
    "BOS": ["celtics", "boston celtics", "jayson tatum", "jaylen brown"],
    "BKN": ["nets", "brooklyn nets"],
    "CHA": ["hornets", "charlotte hornets", "lamelo ball"],
    "CHI": ["bulls", "chicago bulls"],
    "CLE": ["cavaliers", "cavs", "cleveland", "donovan mitchell"],
    "DAL": ["mavericks", "mavs", "dallas", "luka doncic"],
    "DEN": ["nuggets", "denver nuggets", "nikola jokic"],
    "DET": ["pistons", "detroit pistons"],
    "GSW": ["warriors", "golden state", "stephen curry", "steph curry"],
    "HOU": ["rockets", "houston rockets"],
    "IND": ["pacers", "indiana pacers", "tyrese haliburton"],
    "LAC": ["clippers", "la clippers"],
    "LAL": ["lakers", "los angeles lakers", "lebron james", "anthony davis"],
    "MEM": ["grizzlies", "memphis grizzlies", "ja morant"],
    "MIA": ["heat", "miami heat", "jimmy butler"],
    "MIL": ["bucks", "milwaukee bucks", "giannis"],
    "MIN": ["timberwolves", "wolves", "minnesota", "anthony edwards"],
    "NOP": ["pelicans", "new orleans pelicans", "zion williamson"],
    "NYK": ["knicks", "new york knicks", "jalen brunson"],
    "OKC": ["thunder", "oklahoma city", "shai gilgeous-alexander", "sga"],
    "ORL": ["magic", "orlando magic", "paolo banchero"],
    "PHI": ["76ers", "sixers", "philadelphia", "joel embiid"],
    "PHX": ["suns", "phoenix suns", "kevin durant", "devin booker"],
    "POR": ["trail blazers", "blazers", "portland"],
    "SAC": ["kings", "sacramento kings"],
    "SAS": ["spurs", "san antonio spurs", "victor wembanyama", "wemby"],
    "TOR": ["raptors", "toronto raptors"],
    "UTA": ["jazz", "utah jazz"],
    "WAS": ["wizards", "washington wizards"],
}


def try_rss_feeds():
    """Try multiple RSS feed URLs and return whatever works."""
    print("Trying RSS feeds...")
    
    feeds = [
        ("ESPN_NBA", "https://www.espn.com/espn/rss/nba/news"),
        ("ESPN_NBA_2", "https://www.espn.com/blog/feed?blog=nba"),
        ("CBS_NBA", "https://www.cbssports.com/rss/headlines/nba/"),
        ("NBC_NBA", "https://www.nbcsports.com/nba/rss"),
    ]
    
    articles = []
    try:
        import feedparser
        for name, url in feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:20]:
                    summary = getattr(entry, "summary", getattr(entry, "description", ""))
                    summary = re.sub(r"<[^>]+>", "", summary)[:500]
                    articles.append({
                        "SOURCE": name,
                        "TITLE": entry.get("title", ""),
                        "SUMMARY": summary,
                        "LINK": entry.get("link", ""),
                        "PUBLISHED": getattr(entry, "published", ""),
                    })
                if articles:
                    print(f"  {name}: {len(feed.entries)} articles")
            except Exception as e:
                print(f"  {name}: failed ({e})")
    except ImportError:
        print("  feedparser not installed")
    
    return articles


def scrape_espn_nba_news():
    """Scrape NBA headlines directly from ESPN's NBA page."""
    print("Scraping ESPN NBA page...")
    
    try:
        from bs4 import BeautifulSoup
        
        response = requests.get("https://www.espn.com/nba/", headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        articles = []
        # Find headline links
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            
            # Filter for actual article links
            if ("/story/" in href or "/blog/" in href or "/insider/" in href) and len(text) > 20:
                full_url = href if href.startswith("http") else f"https://www.espn.com{href}"
                articles.append({
                    "SOURCE": "ESPN_SCRAPE",
                    "TITLE": text[:200],
                    "SUMMARY": "",
                    "LINK": full_url,
                    "PUBLISHED": datetime.now().strftime("%Y-%m-%d"),
                })
        
        # Deduplicate by title
        seen = set()
        unique = []
        for a in articles:
            if a["TITLE"] not in seen:
                seen.add(a["TITLE"])
                unique.append(a)
        
        print(f"  Found {len(unique)} headlines from ESPN")
        return unique
        
    except Exception as e:
        print(f"  ESPN scrape failed: {e}")
        return []


def scrape_nba_com_news():
    """Scrape headlines from NBA.com."""
    print("Scraping NBA.com news...")
    
    try:
        from bs4 import BeautifulSoup
        
        response = requests.get("https://www.nba.com/news", headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        articles = []
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            
            if "/news/" in href and len(text) > 20 and len(text) < 300:
                full_url = href if href.startswith("http") else f"https://www.nba.com{href}"
                articles.append({
                    "SOURCE": "NBA_COM",
                    "TITLE": text[:200],
                    "SUMMARY": "",
                    "LINK": full_url,
                    "PUBLISHED": datetime.now().strftime("%Y-%m-%d"),
                })
        
        seen = set()
        unique = []
        for a in articles:
            if a["TITLE"] not in seen:
                seen.add(a["TITLE"])
                unique.append(a)
        
        print(f"  Found {len(unique)} headlines from NBA.com")
        return unique
        
    except Exception as e:
        print(f"  NBA.com scrape failed: {e}")
        return []


def tag_teams(df):
    """Tag each article with mentioned NBA teams."""
    print("Tagging articles with team mentions...")
    
    def find_teams(text):
        text_lower = text.lower()
        mentioned = []
        for team_abb, keywords in TEAM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    mentioned.append(team_abb)
                    break
        return ",".join(mentioned) if mentioned else "GENERAL"
    
    df["TEAMS_MENTIONED"] = (df["TITLE"] + " " + df["SUMMARY"]).apply(find_teams)
    return df


def main():
    print("=" * 60)
    print("NBA News Pipeline - Step 5 (Fixed)")
    print("=" * 60)
    
    all_articles = []
    
    # Try RSS feeds first
    rss_articles = try_rss_feeds()
    all_articles.extend(rss_articles)
    
    # Scrape ESPN
    espn_articles = scrape_espn_nba_news()
    all_articles.extend(espn_articles)
    
    # Scrape NBA.com
    nba_articles = scrape_nba_com_news()
    all_articles.extend(nba_articles)
    
    if not all_articles:
        print("\nNo articles from any source. Creating empty schema.")
        df = pd.DataFrame(columns=[
            "SOURCE", "TITLE", "SUMMARY", "LINK", "PUBLISHED", "TEAMS_MENTIONED"
        ])
    else:
        df = pd.DataFrame(all_articles)
        
        # Deduplicate across sources by title similarity
        df = df.drop_duplicates(subset=["TITLE"]).reset_index(drop=True)
        
        # Tag teams
        df = tag_teams(df)
    
    df.to_csv(f"{DATA_DIR}/news_articles.csv", index=False)
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total unique articles: {len(df)}")
    if len(df) > 0:
        print(f"Sources: {df['SOURCE'].value_counts().to_dict()}")
        team_counts = {}
        for teams in df["TEAMS_MENTIONED"]:
            for t in str(teams).split(","):
                if t:
                    team_counts[t] = team_counts.get(t, 0) + 1
        top_teams = sorted(team_counts.items(), key=lambda x: -x[1])[:10]
        print(f"Most mentioned teams: {dict(top_teams)}")
        print()
        print("Sample headlines:")
        for _, row in df.head(5).iterrows():
            print(f"  [{row['SOURCE']}] {row['TITLE'][:80]}")
    print()
    print(f"Saved to {DATA_DIR}/news_articles.csv")


if __name__ == "__main__":
    main()