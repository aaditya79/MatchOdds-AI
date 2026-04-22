"""
Step 4: NBA Twitter Sentiment Pipeline
Pulls recent tweets for NBA teams, runs sentiment analysis, and saves results.

Setup:
    pip install snscrape vaderSentiment pandas

Usage:
    python nba_twitter_pipeline.py

Output:
    data/twitter_sentiment.csv - Tweets with sentiment scores per team
"""

import os
import pandas as pd
from datetime import datetime

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Team search mapping
TEAM_SEARCH_TERMS = {
    "ATL": ["Atlanta Hawks", "Hawks", "#TrueToAtlanta"],
    "BOS": ["Boston Celtics", "Celtics", "#DifferentHere"],
    "BKN": ["Brooklyn Nets", "Nets"],
    "CHA": ["Charlotte Hornets", "Hornets"],
    "CHI": ["Chicago Bulls", "Bulls"],
    "CLE": ["Cleveland Cavaliers", "Cavs"],
    "DAL": ["Dallas Mavericks", "Mavericks", "Mavs"],
    "DEN": ["Denver Nuggets", "Nuggets"],
    "DET": ["Detroit Pistons", "Pistons"],
    "GSW": ["Golden State Warriors", "Warriors", "Dubs"],
    "HOU": ["Houston Rockets", "Rockets"],
    "IND": ["Indiana Pacers", "Pacers"],
    "LAC": ["LA Clippers", "Clippers"],
    "LAL": ["Los Angeles Lakers", "Lakers"],
    "MEM": ["Memphis Grizzlies", "Grizzlies"],
    "MIA": ["Miami Heat", "Heat"],
    "MIL": ["Milwaukee Bucks", "Bucks"],
    "MIN": ["Minnesota Timberwolves", "Timberwolves", "Wolves"],
    "NOP": ["New Orleans Pelicans", "Pelicans", "Pels"],
    "NYK": ["New York Knicks", "Knicks"],
    "OKC": ["Oklahoma City Thunder", "Thunder"],
    "ORL": ["Orlando Magic", "Magic"],
    "PHI": ["Philadelphia 76ers", "Sixers", "76ers"],
    "PHX": ["Phoenix Suns", "Suns"],
    "POR": ["Portland Trail Blazers", "Blazers"],
    "SAC": ["Sacramento Kings", "Kings"],
    "SAS": ["San Antonio Spurs", "Spurs"],
    "TOR": ["Toronto Raptors", "Raptors"],
    "UTA": ["Utah Jazz", "Jazz"],
    "WAS": ["Washington Wizards", "Wizards"],
}


def setup_sentiment_analyzer():
    """Initialize VADER sentiment analyzer."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer()
    except ImportError:
        print("  vaderSentiment not installed. Run: pip install vaderSentiment")
        return None


def setup_twitter_scraper():
    """Check that snscrape is installed."""
    try:
        import snscrape.modules.twitter as sntwitter
        return sntwitter
    except ImportError:
        print("  snscrape not installed. Run: pip install snscrape")
        return None


def build_query(team_terms):
    """
    Build a search query for a team.
    Uses OR between team-related phrases and filters to English tweets.
    """
    quoted_terms = [f'"{term}"' if " " in term else term for term in team_terms]
    joined = " OR ".join(quoted_terms)
    query = f"({joined}) lang:en"
    return query


def pull_team_tweets(sntwitter, team_abb, team_terms, limit=50):
    """Pull recent tweets for a specific team."""
    rows = []
    query = build_query(team_terms)

    try:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i >= limit:
                break

            text = tweet.rawContent.strip() if tweet.rawContent else ""
            rows.append({
                "TEAM": team_abb,
                "SOURCE": "twitter",
                "TEXT": text[:500],
                "TWEET_ID": tweet.id,
                "USERNAME": tweet.user.username if tweet.user else "",
                "LIKE_COUNT": getattr(tweet, "likeCount", 0),
                "RETWEET_COUNT": getattr(tweet, "retweetCount", 0),
                "REPLY_COUNT": getattr(tweet, "replyCount", 0),
                "QUOTE_COUNT": getattr(tweet, "quoteCount", 0),
                "CREATED_UTC": tweet.date.strftime("%Y-%m-%d %H:%M") if tweet.date else "",
                "URL": tweet.url,
            })
    except Exception as e:
        print(f"    Error pulling tweets for {team_abb}: {e}")

    return rows


def pull_general_nba_tweets(sntwitter, limit=50):
    """Pull recent general NBA tweets."""
    rows = []
    query = '(NBA OR "NBA tonight" OR "NBA playoffs" OR "NBA game") lang:en'

    try:
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i >= limit:
                break

            text = tweet.rawContent.strip() if tweet.rawContent else ""
            rows.append({
                "TEAM": "NBA",
                "SOURCE": "twitter",
                "TEXT": text[:500],
                "TWEET_ID": tweet.id,
                "USERNAME": tweet.user.username if tweet.user else "",
                "LIKE_COUNT": getattr(tweet, "likeCount", 0),
                "RETWEET_COUNT": getattr(tweet, "retweetCount", 0),
                "REPLY_COUNT": getattr(tweet, "replyCount", 0),
                "QUOTE_COUNT": getattr(tweet, "quoteCount", 0),
                "CREATED_UTC": tweet.date.strftime("%Y-%m-%d %H:%M") if tweet.date else "",
                "URL": tweet.url,
            })
    except Exception as e:
        print(f"    Error pulling general NBA tweets: {e}")

    return rows


def add_sentiment(rows, analyzer):
    """Add VADER sentiment scores to each row."""
    enriched = []
    for row in rows:
        text = row.get("TEXT", "")
        if not text or not isinstance(text, str):
            sentiment = {"pos": 0, "neg": 0, "neu": 1, "compound": 0}
        else:
            sentiment = analyzer.polarity_scores(text)

        new_row = row.copy()
        new_row["SENTIMENT_POS"] = sentiment["pos"]
        new_row["SENTIMENT_NEG"] = sentiment["neg"]
        new_row["SENTIMENT_NEU"] = sentiment["neu"]
        new_row["SENTIMENT_COMPOUND"] = sentiment["compound"]
        enriched.append(new_row)

    return enriched


def main():
    print("=" * 60)
    print("NBA Twitter Sentiment Pipeline - Step 4")
    print("=" * 60)

    sntwitter = setup_twitter_scraper()
    analyzer = setup_sentiment_analyzer()

    if not sntwitter or not analyzer:
        print()
        print("Creating empty sentiment file with correct schema.")
        empty = pd.DataFrame(columns=[
            "TEAM", "SOURCE", "TEXT", "TWEET_ID", "USERNAME",
            "LIKE_COUNT", "RETWEET_COUNT", "REPLY_COUNT", "QUOTE_COUNT",
            "SENTIMENT_POS", "SENTIMENT_NEG", "SENTIMENT_NEU",
            "SENTIMENT_COMPOUND", "CREATED_UTC", "URL",
        ])
        empty.to_csv(f"{DATA_DIR}/twitter_sentiment.csv", index=False)
        return

    all_rows = []

    print()
    print("Pulling sentiment from Twitter/X...")

    for team_abb, team_terms in TEAM_SEARCH_TERMS.items():
        print(f"  {team_abb}...", end=" ")
        rows = pull_team_tweets(sntwitter, team_abb, team_terms, limit=25)
        rows = add_sentiment(rows, analyzer)
        all_rows.extend(rows)
        print(f"{len(rows)} tweets")

    print("  NBA (general)...", end=" ")
    nba_rows = pull_general_nba_tweets(sntwitter, limit=50)
    nba_rows = add_sentiment(nba_rows, analyzer)
    all_rows.extend(nba_rows)
    print(f"{len(nba_rows)} tweets")

    df = pd.DataFrame(all_rows)
    df.to_csv(f"{DATA_DIR}/twitter_sentiment.csv", index=False)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tweets analyzed: {len(df)}")
    print(f"Teams covered: {df['TEAM'].nunique() if not df.empty else 0}")

    if not df.empty:
        print(f"Average compound sentiment: {df['SENTIMENT_COMPOUND'].mean():.3f}")
        team_means = df.groupby('TEAM')['SENTIMENT_COMPOUND'].mean()
        print(f"Most positive team: {team_means.idxmax()}")
        print(f"Most negative team: {team_means.idxmin()}")
    else:
        print("Average compound sentiment: N/A")
        print("Most positive team: N/A")
        print("Most negative team: N/A")

    print()
    print(f"Saved to {DATA_DIR}/twitter_sentiment.csv")
    print()
    print("Next: Run step 5 (news pipeline)")


if __name__ == "__main__":
    main()