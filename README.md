# MatchOdds AI

**AI-powered NBA pre-game analysis comparing multi-agent debate, single-agent reasoning, and chain-of-thought baselines on real game data.**

> For research purposes only. Not financial advice. Built for STAT GR5293 (GenAI) at Columbia University.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-green)

---

## What It Does

Given an upcoming NBA game, MatchOdds AI gathers pre-game data from multiple sources (stats, injuries, odds, news sentiment, historically similar matchups), runs it through one of three reasoning systems, and produces a structured report with win probabilities, key factors, confidence, and a step-by-step reasoning chain.

The system evaluates three analysis methods side by side:

| Method | Description | LLM Calls |
|--------|------------|-----------|
| **Multi-Agent Debate** | Three specialized agents (Stats, Matchup, Market) with different tool access independently analyze, debate across two rounds, then a moderator synthesizes | ~15-20 |
| **Single Agent (ReAct)** | One agent iteratively decides what data to gather, calls tools, and produces a report when it has enough evidence | ~5-8 |
| **Chain-of-Thought** | All evidence gathered upfront and passed into a single reasoning pass | 1 |

---

## Key Features

**User-facing analysis app**
- Upcoming game selector with team logos
- Live matchup analysis with team snapshots and recent form
- Injury summary and media sentiment
- Win probability visualization with circular gauges
- Key factor breakdown with impact and importance labels
- Side-by-side agent comparison (debate mode)
- Live analysis trace during model execution
- Downloadable JSON reports

**Research and evaluation page**
- Historical backtesting across all three methods
- Model comparison using accuracy, Brier score, log loss, calibration (ECE), F1, precision, recall, MAE
- Calibration plots
- Prediction-level inspection
- Disagreement analysis across methods
- Run-health reporting for incomplete runs

**Infrastructure**
- Model output caching by (game, method) pair
- Retry with exponential backoff for rate limits
- Metadata logging for incomplete or partial runs
- Reproducible evaluation workflow

---

## Architecture

```
+----------------------------------------------------+
|                  Streamlit App                      |
|   Matchup Analysis page   |   Research page        |
+----------------------------------------------------+
| Multi-Agent Debate | Single Agent | CoT Baseline   |
+----------------------------------------------------+
|                  Tool Layer                         |
| get_team_stats | get_head_to_head | get_injuries   |
| get_odds | get_team_sentiment | similar_games      |
+----------------------------------------------------+
|                  Data Layer                         |
| nba_api | ESPN scraping | The Odds API | ChromaDB  |
+----------------------------------------------------+
```

**Multi-Agent Debate:**
- **Stats Agent** -- season record, recent form, efficiency, plus/minus. Only accesses quantitative data.
- **Matchup Agent** -- injuries, context, and matchup-specific factors. Only accesses contextual data.
- **Market Agent** -- starts from bookmaker framing and pricing when available.

Agents debate across two rounds and a moderator synthesizes the final prediction.

---

## Data Sources

| Source | Provider | Purpose |
|--------|----------|---------|
| Game and Team Stats | `nba_api` | Historical game logs, team performance, standings, head-to-head |
| Injuries | ESPN (scraped) | Current player availability |
| Betting Odds | The Odds API | Live odds from multiple sportsbooks |
| Historical Similar Games | ChromaDB vector store | Retrieval of similar matchup contexts |
| News / Sentiment | ESPN, NBA.com (scraped) | Recent team-level coverage and sentiment |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/aaditya79/MatchOdds-AI.git
cd MatchOdds-AI
pip install -r requirements.txt
```

### 2. Set API keys

```bash
# LLM backend (pick one)
export ANTHROPIC_API_KEY="sk-ant-..."
# or
export OPENAI_API_KEY="sk-..."

# Optional: live odds
export ODDS_API_KEY="your_key_here"
```

### 3. Build the data pipeline

Run these in order:

```bash
python3 nba_data_pipeline.py         # historical NBA data
python3 nba_injury_pipeline.py       # current injuries
python3 nba_odds_pipeline.py         # live odds
python3 nba_news_pipeline.py         # news + sentiment inputs
python3 nba_vector_store.py          # ChromaDB build
```

---

## Running the App

```bash
streamlit run Matchup_Analysis.py
```

This launches the main user-facing app at `http://localhost:8501`.

The research and evaluation page is accessible from the sidebar within the app.

---

## Backtesting and Evaluation

The research workflow evaluates all three reasoning methods on historical games using only information available before each game.

**Metrics tracked:**
- Accuracy, precision, recall, F1
- Log loss, Brier score, MAE on predicted probabilities
- Calibration / ECE
- Prediction gap and confidence patterns

**Run a backtest:**

```bash
python3 nba_backtest.py --n-games 25 --season 2025-26
```

**Outputs:**
- `data/backtest_predictions.csv` -- per-game predictions and outcomes
- `data/backtest_summary.csv` -- aggregated metrics by method
- `data/backtest_calibration.csv` -- calibration bin data
- `data/backtest_run_metadata.json` -- run metadata and completion status

**Robustness features:**
- Cache by game/method in `data/backtest_cache/`
- Retry with exponential backoff for transient API failures
- Incomplete-run reporting in the research UI

---

## Run Individual Components

```bash
python3 nba_agent.py                 # single-agent analysis
python3 nba_multi_agent.py           # multi-agent debate
python3 nba_cot_baseline.py          # chain-of-thought baseline
python3 nba_backtest.py              # historical backtest
```

---

## Project Structure

```
matchodds-ai/
├── Matchup_Analysis.py              # main Streamlit matchup analysis app
├── pages/
│   └── Research_Evaluation.py       # research / backtesting page
├── nba_data_pipeline.py             # Step 1: historical nba_api data collection
├── nba_injury_pipeline.py           # Step 2: ESPN injury scraping
├── nba_odds_pipeline.py             # Step 3: The Odds API integration
├── nba_news_pipeline.py             # Step 5: news scraping + sentiment inputs
├── nba_vector_store.py              # Step 6: ChromaDB vector store
├── nba_agent.py                     # Step 7: single-agent reasoning system
├── nba_multi_agent.py               # Step 8: multi-agent debate system
├── nba_cot_baseline.py              # Step 9: chain-of-thought baseline
├── nba_backtest.py                  # historical evaluation script
├── data/
│   ├── game_logs.csv
│   ├── team_stats.csv
│   ├── standings.csv
│   ├── head_to_head.csv
│   ├── injuries.csv
│   ├── odds_live.csv
│   ├── news_articles.csv
│   ├── team_sentiment.csv
│   ├── backtest_predictions.csv
│   ├── backtest_summary.csv
│   ├── backtest_calibration.csv
│   ├── backtest_run_metadata.json
│   └── backtest_cache/
├── chroma_db/                       # ChromaDB persistent storage
├── requirements.txt
└── README.md
```

---

## Research Questions

**RQ1:** How does prediction quality relate to information density?

**RQ2:** Does multi-agent debate with differentiated reasoning outperform simpler single-agent baselines?

**RQ3 (Extension):** How well calibrated are the model probabilities, not just how accurate are the picks?

**RQ4 (Extension):** When the three reasoning styles disagree, what kinds of matchups create the largest uncertainty?

---

## Requirements

```
nba_api
pandas
requests
beautifulsoup4
feedparser
chromadb
anthropic              # or openai
streamlit
matplotlib
```

Optional:

```
vaderSentiment
praw
```

---

## Team

- **Pranav Jain** -- data pipeline, vector store, CoT baseline
- **Aaditya Pai** -- agent architecture, multi-agent debate, backtesting, evaluation
- **Tanish Patel** -- Streamlit app, deployment, UI/report quality

STAT GR5293: Generative AI Using LLMs | Spring 2026 | Columbia University

---

## References

1. Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., and Mordatch, I. (2024). Improving factuality and reasoning in language models through multiagent debate. *ICML 2024*.
2. Lewis, P. et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS 2020*.
3. Wei, J. et al. (2022). Chain-of-thought prompting elicits reasoning in large language models. *NeurIPS 2022*.
4. Yao, S. et al. (2023). ReAct: Synergizing reasoning and acting in language models. *ICLR 2023*.
5. Gneiting, T. and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *JASA*, 102(477), 359-378.
