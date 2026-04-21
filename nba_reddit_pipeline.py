"""
Step 4: NBA Reddit Sentiment Pipeline
Pulls posts and comments from r/nba and team subreddits, runs sentiment analysis.

Setup:
    1. Create a Reddit app at https://www.reddit.com/prefs/apps/
       - Choose "script" type
       - Note your client_id and client_secret
    2. Set environment variables:
       export REDDIT_CLIENT_ID="your_client_id"
       export REDDIT_CLIENT_SECRET="your_client_secret"
       export REDDIT_USER_AGENT="nba_betting_analyst:v1.0 (by /u/your_username)"

Usage:
    pip install praw vaderSentiment pandas
    python nba_reddit_pipeline.py

Output:
    data/reddit_sentiment.csv - Posts with sentiment scores per team/game
"""

import os
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Reddit config
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "nba_betting_analyst:v1.0")

# Team subreddit mapping
TEAM_SUBREDDITS = {
    "ATL": "AtlantaHawks", "BOS": "bostonceltics", "BKN": "GoNets",
    "CHA": "CharlotteHornets", "CHI": "chicagobulls", "CLE": "clevelandcavs",
    "DAL": "Mavericks", "DEN": "denvernuggets", "DET": "DetroitPistons",
    "GSW": "warriors", "HOU": "rockets", "IND": "pacers",
    "LAC": "LAClippers", "LAL": "lakers", "MEM": "memphisgrizzlies",
    "MIA": "heat", "MIL": "MkeBucks", "MIN": "timberwolves",
    "NOP": "NOLAPelicans", "NYK": "NYKnicks", "OKC": "Thunder",
    "ORL": "OrlandoMagic", "PHI": "sixers", "PHX": "suns",
    "POR": "ripcity", "SAC": "kings", "SAS": "NBASpurs",
    "TOR": "torontoraptors", "UTA": "UtahJazz", "WAS": "washingtonwizards",
}


def setup_reddit():
    """Initialize the Reddit API client."""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("  Reddit credentials not set. Set environment variables:")
        print("    REDDIT_CLIENT_ID")
        print("    REDDIT_CLIENT_SECRET")
        print("    REDDIT_USER_AGENT")
        print("  Get credentials at https://www.reddit.com/prefs/apps/")
        return None

    try:
        import praw
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        # Test connection
        reddit.subreddit("nba").id
        print("  Reddit connection successful.")
        return reddit
    except Exception as e:
        print(f"  Reddit connection failed: {e}")
        return None


def setup_sentiment_analyzer():
    """Initialize VADER sentiment analyzer."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer()
    except ImportError:
        print("  vaderSentiment not installed. Run: pip install vaderSentiment")
        return None


def pull_subreddit_posts(reddit, subreddit_name, limit=50):
    """Pull recent posts from a subreddit."""
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = []
        for post in subreddit.hot(limit=limit):
            posts.append({
                "SUBREDDIT": subreddit_name,
                "POST_ID": post.id,
                "TITLE": post.title,
                "SELFTEXT": post.selftext[:500] if post.selftext else "",
                "SCORE": post.score,
                "NUM_COMMENTS": post.num_comments,
                "CREATED_UTC": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M"),
                "URL": post.url,
            })
        return posts
    except Exception as e:
        print(f"    Error pulling from r/{subreddit_name}: {e}")
        return []


def pull_game_thread_comments(reddit, search_query, limit=100):
    """
    Search r/nba for game threads mentioning specific teams
    and pull top comments.
    """
    try:
        subreddit = reddit.subreddit("nba")
        posts = []
        for post in subreddit.search(search_query, sort="new", time_filter="week", limit=5):
            # Get top-level comments
            post.comments.replace_more(limit=0)
            for comment in post.comments[:limit]:
                posts.append({
                    "SUBREDDIT": "nba",
                    "POST_ID": post.id,
                    "POST_TITLE": post.title,
                    "COMMENT_ID": comment.id,
                    "COMMENT_BODY": comment.body[:500],
                    "COMMENT_SCORE": comment.score,
                    "CREATED_UTC": datetime.fromtimestamp(comment.created_utc).strftime("%Y-%m-%d %H:%M"),
                })
        return posts
    except Exception as e:
        print(f"    Error searching r/nba for '{search_query}': {e}")
        return []


def analyze_sentiment(texts, analyzer):
    """Run VADER sentiment analysis on a list of texts."""
    results = []
    for text in texts:
        if not text or not isinstance(text, str):
            results.append({"neg": 0, "neu": 1, "pos": 0, "compound": 0})
            continue
        scores = analyzer.polarity_scores(text)
        results.append(scores)
    return results


def pull_team_sentiment(reddit, analyzer, team_abb, team_sub, limit=25):
    """Pull posts and sentiment for a specific team."""
    rows = []

    # Pull from team subreddit
    posts = pull_subreddit_posts(reddit, team_sub, limit=limit)
    for post in posts:
        text = f"{post['TITLE']} {post['SELFTEXT']}"
        sentiment = analyzer.polarity_scores(text)
        rows.append({
            "TEAM": team_abb,
            "SOURCE": f"r/{team_sub}",
            "TEXT": post["TITLE"][:200],
            "SCORE": post["SCORE"],
            "NUM_COMMENTS": post["NUM_COMMENTS"],
            "SENTIMENT_POS": sentiment["pos"],
            "SENTIMENT_NEG": sentiment["neg"],
            "SENTIMENT_NEU": sentiment["neu"],
            "SENTIMENT_COMPOUND": sentiment["compound"],
            "CREATED_UTC": post["CREATED_UTC"],
        })

    return rows


def main():
    print("=" * 60)
    print("NBA Reddit Sentiment Pipeline - Step 4")
    print("=" * 60)

    # Setup
    reddit = setup_reddit()
    analyzer = setup_sentiment_analyzer()

    if not reddit or not analyzer:
        print()
        print("Creating empty sentiment file with correct schema.")
        print("Set up Reddit credentials and re-run to populate.")
        empty = pd.DataFrame(columns=[
            "TEAM", "SOURCE", "TEXT", "SCORE", "NUM_COMMENTS",
            "SENTIMENT_POS", "SENTIMENT_NEG", "SENTIMENT_NEU",
            "SENTIMENT_COMPOUND", "CREATED_UTC",
        ])
        empty.to_csv(f"{DATA_DIR}/reddit_sentiment.csv", index=False)
        return

    # Pull sentiment for each team
    all_rows = []
    print()
    print("Pulling sentiment from team subreddits...")

    for team_abb, team_sub in TEAM_SUBREDDITS.items():
        print(f"  {team_abb} (r/{team_sub})...", end=" ")
        try:
            rows = pull_team_sentiment(reddit, analyzer, team_abb, team_sub, limit=15)
            all_rows.extend(rows)
            print(f"{len(rows)} posts")
        except Exception as e:
            print(f"error: {e}")

    # Also pull from r/nba main
    print("  r/nba (main sub)...", end=" ")
    nba_posts = pull_subreddit_posts(reddit, "nba", limit=50)
    for post in nba_posts:
        text = f"{post['TITLE']} {post['SELFTEXT']}"
        sentiment = analyzer.polarity_scores(text)
        all_rows.append({
            "TEAM": "NBA",  # general, not team-specific
            "SOURCE": "r/nba",
            "TEXT": post["TITLE"][:200],
            "SCORE": post["SCORE"],
            "NUM_COMMENTS": post["NUM_COMMENTS"],
            "SENTIMENT_POS": sentiment["pos"],
            "SENTIMENT_NEG": sentiment["neg"],
            "SENTIMENT_NEU": sentiment["neu"],
            "SENTIMENT_COMPOUND": sentiment["compound"],
            "CREATED_UTC": post["CREATED_UTC"],
        })
    print(f"{len(nba_posts)} posts")

    # Save
    df = pd.DataFrame(all_rows)
    df.to_csv(f"{DATA_DIR}/reddit_sentiment.csv", index=False)

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total posts analyzed: {len(df)}")
    print(f"Teams covered: {df['TEAM'].nunique()}")
    print(f"Average compound sentiment: {df['SENTIMENT_COMPOUND'].mean():.3f}")
    print(f"Most positive team: {df.groupby('TEAM')['SENTIMENT_COMPOUND'].mean().idxmax()}")
    print(f"Most negative team: {df.groupby('TEAM')['SENTIMENT_COMPOUND'].mean().idxmin()}")
    print()
    print(f"Saved to {DATA_DIR}/reddit_sentiment.csv")
    print()
    print("Next: Run step 5 (news pipeline)")


if __name__ == "__main__":
    main()
