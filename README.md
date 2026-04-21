# 🏀 MatchOdds AI

**AI-powered NBA pre-game betting analyst using multi-agent debate, RAG, and agentic reasoning.**

> ⚠️ For research purposes only. Not financial advice. Built for STAT GR5293 (GenAI) at Columbia University.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-green)

---

## What It Does

Given an upcoming NBA game, MatchOdds AI gathers data from multiple sources (odds, stats, injuries, news, historical games), retrieves similar matchups from a vector database, and produces a structured betting report with win probabilities and step-by-step reasoning.

The system compares three analysis approaches:

| Method | How It Works | LLM Calls |
|--------|-------------|-----------|
| **Multi-Agent Debate** | Three specialized agents (Stats, Matchup, Market) with different tool access independently analyze, debate for 2 rounds, and a moderator synthesizes | ~15-20 |
| **Single Agent (ReAct)** | One agent iteratively decides what data to gather and when it has enough to report | ~5-8 |
| **Chain-of-Thought** | All data gathered upfront, single-pass reasoning | 1 |

## Architecture

```
┌─────────────────────────────────────────────┐
│                Streamlit App                 │
├─────────────────────────────────────────────┤
│  Multi-Agent Debate  │  ReAct  │    CoT     │
├──────────────────────┴─────────┴────────────┤
│              Agent Tools Layer               │
│  get_team_stats │ get_injuries │ get_odds   │
│  get_head_to_head │ search_similar_games    │
├─────────────────────────────────────────────┤
│              Data Layer                      │
│  nba_api │ ESPN │ Odds API │ ChromaDB       │
└─────────────────────────────────────────────┘
```

**Multi-Agent Debate:**
- **Stats Agent** — focuses on scoring, defense, pace, efficiency. Only accesses quantitative data.
- **Matchup Agent** — focuses on injuries, schedule, travel, rest, context. Only accesses contextual data.
- **Market Agent** — starts from bookmaker odds, cross-checks with any source.

Agents debate across 2 rounds where they see and respond to each other's arguments before a moderator synthesizes the final prediction.

## Data Sources

All sources are free. `nba_api` handles most of the heavy lifting with no rate limits.

| Source | Provider | Purpose |
|--------|----------|---------|
| Game & Player Stats | `nba_api` | Box scores, team/player stats, game logs, standings, H2H (stats agent) |
| Injuries | `nbainjuries` (official NBA reports) | Player status, injury type (stats + matchup agents) |
| Betting Odds | The Odds API (free tier, **live demo only**); Kaggle (**historical evaluation**) | Cross-sportsbook odds, implied probabilities, line movement |
| Sentiment | Reddit PRAW (r/nba, team subs) | Fan expectations, hype level, injury reactions (matchup agent) |
| News | ESPN, Bleacher Report RSS | Late scratches, coach quotes, rest decisions (matchup agent) |
| Vector Store | ChromaDB (built from `nba_api` data) | Historically similar games by metadata (all agents) |

Evaluation sample: 150–200 games from recent NBA seasons via Kaggle datasets. The live Odds API free tier is reserved for the demo app.

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/matchodds-ai.git
cd matchodds-ai
pip install -r requirements.txt
```

### 2. Set API keys

```bash
# LLM (pick one)
export ANTHROPIC_API_KEY="sk-ant-..."
# or
export OPENAI_API_KEY="sk-..."

# Odds (optional, for live odds)
export ODDS_API_KEY="your_key"
```

### 3. Build the data pipeline

```bash
python3 nba_data_pipeline.py      # Step 1: Pull 4 seasons of NBA data
python3 nba_injury_pipeline.py    # Step 2: Scrape current injuries
python3 nba_odds_pipeline.py      # Step 3: Pull live odds
python3 nba_reddit_pipeline.py    # Step 4: Scrape Reddit sentiment (optional)
python3 nba_news_pipeline.py      # Step 5: Scrape news headlines
python3 nba_vector_store.py       # Step 6: Build ChromaDB vector store
```

### 4. Run the app

```bash
streamlit run nba_streamlit_app.py
```

Opens at `http://localhost:8501`.

### 5. Run individual components

```bash
python3 nba_agent.py              # Single agent analysis
python3 nba_multi_agent.py        # Multi-agent debate
python3 nba_cot_baseline.py       # Chain-of-thought baseline
```

## Project Structure

```
matchodds-ai/
├── nba_data_pipeline.py       # Step 1: nba_api data collection
├── nba_injury_pipeline.py     # Step 2: ESPN injury scraping
├── nba_odds_pipeline.py       # Step 3: The Odds API integration
├── nba_reddit_pipeline.py     # Step 4: Reddit sentiment (optional)
├── nba_news_pipeline.py       # Step 5: News scraping
├── nba_vector_store.py        # Step 6: ChromaDB vector store
├── nba_agent.py               # Step 7: ReAct agent with tools
├── nba_multi_agent.py         # Step 8: Multi-agent debate system
├── nba_cot_baseline.py        # Step 9: Chain-of-thought baseline
├── nba_streamlit_app.py       # Step 10: Streamlit web app
├── data/                      # Generated CSV data files
│   ├── game_logs.csv
│   ├── team_stats.csv
│   ├── standings.csv
│   ├── head_to_head.csv
│   ├── injuries.csv
│   ├── odds_live.csv
│   └── news_articles.csv
├── chroma_db/                 # ChromaDB persistent storage
├── requirements.txt
└── README.md
```

## Research Questions

**RQ1:** How does prediction quality relate to information density? For each game we measure how much data the agent gathered (Reddit comments, news articles, vector store hits, context tokens) and plot prediction quality against it. Does the agent do better on high-profile games with more to work with, or on low-profile games where the market may be softer?

**RQ2:** Does a multi-agent debate with differentiated tool access outperform single-agent chain-of-thought reasoning?

**RQ3:** Which data sources (live stats, vector store historical context, sentiment, news, injury reports) contribute most to prediction quality?

## Evaluation

- **Prediction calibration:** Brier score and calibration curves for CoT vs. multi-agent debate. Market implied probability is the baseline.
- **Information density vs. prediction quality:** Count data gathered per game (Reddit comments, news articles, vector store hits, context tokens) and plot Brier score against it, segmented by game profile.
- **Ablation:** Remove one data source at a time and measure Brier score impact. Vector store on vs. off tested specifically to isolate the value of historical retrieval.
- **Report quality:** Score 20–30 reports on factual accuracy, completeness, reasoning quality, and actionability.
- **Secondary breakdowns:** Results sliced by back-to-back games, star player absences, and home vs. away.

## Requirements

```
nba_api
pandas
requests
beautifulsoup4
feedparser
chromadb
anthropic        # or openai
streamlit
vaderSentiment   # optional, for Reddit sentiment
praw             # optional, for Reddit
```

## Team

- **Pranav Jain** — `nba_api` and injury tool wrappers, ChromaDB vector store, CoT baseline, ablation experiments.
- **Aaditya Pai** — Odds API, Reddit PRAW, news RSS integration, agent prompts, ReAct loop, multi-agent debate, main evaluation pipeline.
- **Tanish Patel** — Streamlit app, report layout, evaluation framework (Brier, calibration, info density), deployment, report quality review.

STAT GR5293 | Spring 2026 | Columbia University

## References

1. Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., and Mordatch, I. (2024). Improving factuality and reasoning in language models through multiagent debate. *ICML 2024*.
2. Lewis, P. et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS 2020*.
3. Wei, J. et al. (2022). Chain-of-thought prompting elicits reasoning in large language models. *NeurIPS 2022*.
4. Yao, S. et al. (2023). ReAct: Synergizing reasoning and acting in language models. *ICLR 2023*.
5. Gneiting, T. and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *JASA*, 102(477), 359-378.
