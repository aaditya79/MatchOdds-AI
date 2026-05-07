# MatchOdds AI

**An agentic RAG system for NBA pre-game betting analysis. Compares chain-of-thought, single ReAct agent, and multi-agent debate on 132 real historical games.**

> For research purposes only. Not financial advice. Built for STAT GR5293 (Generative AI Using LLMs) at Columbia University, Spring 2026.

---

## What It Does

Given an upcoming NBA game, MatchOdds AI pulls pre-game data from six sources, passes it through one of three reasoning systems, and produces a structured report with win probabilities, key factors, a bookmaker market comparison, historically similar games, and a step-by-step reasoning trace.

The system was built as a research platform to answer three questions:

- **RQ1** — Does more pre-game information improve prediction quality, or do high-profile games become harder due to efficient markets?
- **RQ2** — Does multi-agent debate with differentiated tool access outperform a single chain-of-thought pass?
- **RQ3** — Which data sources actually contribute to Brier score, and which are redundant?

---

## Evaluation Results (132 games, 2024–25 NBA season)

| Method | Brier ↓ | Log Loss ↓ | ECE ↓ | Accuracy ↑ |
|---|---|---|---|---|
| **CoT Baseline** | **0.228** | **0.646** | **0.068** | **61.4%** |
| Multi-Agent Debate | 0.283 | 0.771 | 0.167 | 52.3% |
| Single ReAct Agent | 0.297 | 0.811 | 0.205 | 52.8% |
| Random (50/50) | 0.250 | — | — | — |

CoT is the only method that beats the random-predictor Brier baseline of 0.25. Both agent-based methods fall below it, driven by a home/away label inversion in their structured JSON outputs. CoT avoids this by producing a single coherent generation.

**Ablation (RQ3) — CoT Brier delta when each source is disabled:**

| Disabled Source | Brier | Delta |
|---|---|---|
| h2h | 0.2385 | +0.010 |
| stats | 0.2352 | +0.007 |
| vector_store | 0.2338 | +0.006 |
| injuries | 0.2252 | −0.003 (no historical data) |
| odds | 0.2263 | −0.002 (no historical data) |
| news | 0.2175 | −0.011 (no historical data) |
| youtube | 0.2108 | −0.017 (no historical data) |

The three sources with real historical snapshots (h2h, stats, vector store) all hurt performance when removed. The other four return no data for past games, so their deltas are sampling noise.

**Total API cost:** $49.84 — $26.09 for the 132-game main eval (all 3 methods, 8,356 calls) + ~$23.75 for 7 CoT-only ablation sweeps. All inference uses Claude Haiku 4.5.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           React Frontend (Vite + TS)         │
│  Matchup Analysis | Research | Simulation    │
└─────────────────┬───────────────────────────┘
                  │ HTTP / SSE
┌─────────────────▼───────────────────────────┐
│              FastAPI Backend                 │
│  /games  /analysis  /backtest  /pipelines   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│    Three Reasoning Methods (Claude Haiku 4.5)│
│  CoT Baseline | Single ReAct | Multi-Agent  │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           Tool Layer (6 functions)           │
│  get_team_stats    | get_head_to_head       │
│  get_injuries      | get_odds               │
│  get_team_sentiment| search_similar_games   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│                Data Layer                    │
│  nba_api (11,465 games, 9 seasons)          │
│  ChromaDB (22,930 embedded game docs)       │
│  The Odds API + Kaggle historical odds      │
│  nbainjuries package                        │
│  ESPN/CBS RSS feeds + VADER sentiment       │
│  YouTube Data API v3 + Reddit public JSON   │
└─────────────────────────────────────────────┘
```

### Three Reasoning Methods

| Method | LLM Calls/Game | Description |
|---|---|---|
| **CoT Baseline** | 1 | All six tools called deterministically upfront; single structured prompt passed to LLM |
| **Single ReAct Agent** | ~5–12 | Model plans, calls tools one at a time, observes results, decides when to finalize |
| **Multi-Agent Debate** | ~15–20 | Stats Agent + Matchup Agent + Market Agent each have differentiated tool access; 2 debate rounds; moderator synthesizes |

All tools accept an `as_of_date` parameter. The backtest harness wraps every tool call so historical games only see data available before game day — no leakage.

---

## Data Sources

| Source | Details |
|---|---|
| `nba_api` | 11,465 game records across 9 seasons (2017–18 through 2025–26, including playoffs) |
| ChromaDB vector store | 22,930 embedded game documents with metadata filters (back-to-back, rest days, home/away, season) |
| nbainjuries package | Current player availability (point-in-time; no per-day historical snapshots) |
| The Odds API | Live cross-sportsbook moneyline odds; Kaggle historical dataset for backtesting |
| ESPN + CBS Sports RSS | 81 articles ingested; VADER sentiment scoring per team |
| YouTube Data API v3 | Comment counts and sentiment on NBA highlight videos |
| Reddit public JSON | 1,567 comments via public endpoint (OAuth PRAW was blocked on university network) |

**Note on backtest:** Only h2h, stats, and vector store provide real historical signals. Injuries, sentiment, odds, and YouTube return "no historical snapshot" for past games, so the backtest effectively evaluates a 3-source system for those runs.

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the React frontend)
- Java (arm64 OpenJDK 18 required for `nbainjuries` on Apple Silicon):
  ```bash
  brew install openjdk@18
  export JAVA_HOME=/opt/homebrew/opt/openjdk@18/libexec/openjdk.jdk/Contents/Home
  ```

### 1. Clone and install Python dependencies

```bash
git clone https://github.com/aaditya79/MatchOdds-AI.git
cd MatchOdds-AI
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set API keys

```bash
cp .env.example .env
# Fill in:
# ANTHROPIC_API_KEY=sk-ant-...
# ODDS_API_KEY=...
# YOUTUBE_API_KEY=...
```

### 3. Populate data (run once)

```bash
python nba_data_pipeline.py       # ~60 min, nba_api rate limits
python nba_vector_store.py        # embeds 22,930 game docs into ChromaDB
python nba_news_pipeline.py       # ESPN/CBS RSS
python nba_reddit_pipeline.py     # Reddit public JSON
python nba_injury_pipeline.py     # requires JAVA_HOME set
python nba_odds_pipeline.py       # The Odds API
```

### 4. Start the backend

```bash
cd backend
pip install -r requirements.txt
./run.sh
# FastAPI runs at http://localhost:8000
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
# React app runs at http://localhost:5173
```

---

## Backtesting

```bash
# Smoke test (~5 games, ~$0.30)
python nba_backtest.py --n-games 5 --season 2024-25

# Full eval (132 games, ~17 hours, ~$26)
python nba_backtest.py --n-games 150 --season 2024-25

# Ablation sweep (disable one source at a time, CoT only)
for src in h2h stats vector_store odds injuries news youtube; do
  python nba_backtest.py --n-games 150 --season 2024-25 --disable-source "$src"
done
```

Results are cached by `(game_id, method, ablation)` key — interrupted runs resume without duplicating API calls.

**Output files:**
- `data/backtest_predictions.csv` — per-game predictions and outcomes
- `data/backtest_summary.csv` — aggregated metrics by method
- `data/backtest_calibration.csv` — 5-bin calibration data
- `data/backtest_ablation_<source>.csv` — per-ablation results
- `data/backtest_run_metadata.json` — run stats and completion status
- `data/llm_calls.jsonl` — per-call cost log

---

## Project Structure

```
MatchOdds-AI/
├── frontend/                    # React + TypeScript UI (Vite)
│   └── src/pages/
│       ├── MatchupPage.tsx      # main analysis UI
│       ├── ResearchPage.tsx     # backtest results, calibration, ablation
│       └── SimulationPage.tsx   # betting simulation
├── backend/                     # FastAPI server
│   └── app/
│       ├── routers/             # /games /analysis /backtest /pipelines
│       └── services/            # analysis, backtest, LLM wrappers
├── nba_agent.py                 # single ReAct agent
├── nba_multi_agent.py           # multi-agent debate (3 agents x 2 rounds)
├── nba_cot_baseline.py          # chain-of-thought baseline
├── nba_backtest.py              # evaluation harness
├── nba_cost_logger.py           # per-call cost tracking
├── nba_data_pipeline.py         # nba_api historical data
├── nba_vector_store.py          # ChromaDB indexing
├── nba_injury_pipeline.py       # nbainjuries scraper
├── nba_odds_pipeline.py         # The Odds API + Kaggle
├── nba_news_pipeline.py         # ESPN/CBS RSS + VADER
├── nba_reddit_pipeline.py       # Reddit public JSON
├── nba_youtube_pipeline.py      # YouTube Data API v3
├── data/sample/                 # example CSVs for reproducibility
├── fig_brier_bar.png            # publication figure
├── fig_calibration.png          # publication figure
├── fig_density.png              # publication figure
├── fig_ablation.png             # publication figure
├── report.tex                   # LaTeX source
├── report.pdf                   # compiled paper
└── requirements.txt
```

---

## Key Findings

- **CoT wins on every metric.** One structured pass over pre-gathered evidence outperforms both iterative tool-calling and multi-agent debate on Brier, log loss, ECE, and accuracy.
- **Both agent methods fall below the random baseline on Brier.** The home/away label inversion in their structured JSON outputs systematically corrupts predictions. CoT avoids this by producing a single coherent generation with no intermediate JSON parsing.
- **More data does not help.** Information density (context tokens, vector hits, article count) shows near-zero correlation with Brier score (Pearson r = +0.058). High-profile games are marginally harder to predict, consistent with efficient markets tightening the lines.
- **h2h, stats, and vector store are the only sources that matter for backtesting.** The other four sources return no historical snapshots, so their ablation deltas reflect sample noise rather than genuine signal.
- **Agents degrade on back-to-back games.** CoT is stable (Brier delta −0.011 on B2B games); multi-agent (+0.033) and single agent (+0.073) both degrade substantially.

---

## Team

| Member | Contributions |
|---|---|
| **Aaditya Pai** | Agent architecture, multi-agent debate, backtesting harness, evaluation, ablations, report |
| **Pranav Jain** | Data pipelines, vector store, CoT baseline |
| **Tanish Patel** | React frontend, FastAPI backend, deployment |

STAT GR5293: Generative AI Using LLMs | Spring 2026 | Columbia University

---

## References

1. Du et al. (2024). Improving factuality and reasoning in language models through multiagent debate. *ICML 2024*.
2. Lewis et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *NeurIPS 2020*.
3. Wei et al. (2022). Chain-of-thought prompting elicits reasoning in large language models. *NeurIPS 2022*.
4. Yao et al. (2023). ReAct: Synergizing reasoning and acting in language models. *ICLR 2023*.
5. Hutto & Gilbert (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *ICWSM 2014*.
6. Qiu, E. (2024). NBA odds and scores dataset. Kaggle.
