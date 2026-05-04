# MatchOdds AI — Status & Handoff

**STAT GR5293 | Spring 2026 | Pranav Jain, Aaditya Pai, Tanish Patel**
**Updated: 2026-05-03**

This document is the source of truth for **what is done, what is not done, and exactly what each team member needs to do next**. Open the section that's relevant to you. Plain-English explanation first, then a pastable Claude Code prompt.

---

## Part 1: Proposal compliance (line by line)

For every claim in `proposal.pdf`, exactly where we stand.

### Research Questions

| RQ | Claim | Status | Notes |
|---|---|---|---|
| RQ1 | How does prediction quality relate to information density? | 🟡 **Infrastructure ready, results pending** | Per-game info_density tracking is built (4 signals: youtube_comments, news_articles, vector_hits, context_tokens). Ready to run on the 150-game eval. |
| RQ2 | Does multi-agent debate beat CoT? | 🟡 **Infrastructure ready, results pending** | Real iterative debate per Du et al. is built. CoT baseline is built. Backtest is wired to call them both. Ready to run. |
| RQ3 | Which data sources contribute most? | 🟡 **Infrastructure ready, results pending** | Ablation flag (`--disable-source <name>`) supports all 7 sources. Ready to run. |

### Deliverables (proposal Section 2)

| # | Deliverable | Status | Notes |
|---|---|---|---|
| 1 | Agentic RAG pipeline (vector store + live tools) | ✅ **DONE** | `nba_agent.py` ReAct loop with 6 tools. ChromaDB has 22,930 game documents. |
| 2 | Multi-agent debate (3 agents, differentiated tool access, iterative rounds) | ✅ **DONE** | `nba_multi_agent.py` — stats / matchup / market agents. Iterative debate with convergence check. |
| 3 | Chain-of-thought baseline | ✅ **DONE** | `nba_cot_baseline.py` — single-pass reasoning. |
| 4 | Evaluation (Brier, calibration, info density, ablation, report quality) | 🟡 **CODE DONE, RESULTS PENDING** | All 5 eval methods coded. Only the report quality rubric requires manual scoring; everything else is one backtest run away. |
| 5 | Deployed Streamlit app | 🟡 **Local works, cloud deploy pending** | Backend complete. Tanish needs to add UI features + deploy to Streamlit Cloud. |
| 6 | Open-source GitHub repo with documentation and example reports | 🟡 **Repo + docs partial; example reports pending** | Repo exists with README, AUDIT.md, RESULTS.md scaffold, this file. Example reports come after eval lands. |

### Technical Approach (proposal Section 3)

| Claim | Status |
|---|---|
| Streamlit app listing tonight's/upcoming games | ✅ DONE — game dropdown populated from live odds |
| Per-game report with odds, key factors, historical precedent, fan sentiment, agent assessment, divergence flag | 🟡 PARTIAL — missing sections in UI: odds compare table, divergence flag, "similar past games" display (Tanish's work) |
| ChromaDB vector store with NBA game metadata | ✅ DONE — 22,930 documents with B2B, rest, home/away, plus_minus, etc. metadata |
| ReAct-style agent loop with 6 tools | ✅ DONE |
| Multi-agent: 3 differentiated agents, iterative debate, moderator synthesis | ✅ DONE per Du et al. |
| CoT baseline single-pass reasoning | ✅ DONE |

### Data Sources (proposal Section 4)

| Source | Proposal | Status |
|---|---|---|
| Game/Player Stats | `nba_api` (free) | ✅ DONE — 11,465 games × 9 seasons (2017-18 to 2025-26 incl. playoffs) |
| Injuries | `nbainjuries` package | ✅ DONE — 12 active injuries pulled |
| Betting Odds | The Odds API (live) + Kaggle (historical) | ✅ DONE — 183 live odds rows, Kaggle loader ready |
| Sentiment | Reddit PRAW | ✅ DONE — Reddit via **public JSON endpoint** (no app required, since OAuth-app path was blocked). 1,567 comments analyzed across 31 subs. Documented as substitution. |
| News | ESPN, Bleacher Report RSS | 🟡 PARTIAL — ESPN + CBS RSS done (81 articles). Bleacher Report not yet added (~30 min addition). |
| Vector Store | ChromaDB | ✅ DONE — 22,930 game documents indexed |

### Evaluation Plan (proposal Section 5)

| Method | Status |
|---|---|
| Prediction calibration (Brier + calibration curves, market baseline) | 🟡 Code done, results pending eval run |
| Info density vs prediction quality (RQ1 plot) | 🟡 Code done (`info_density` dict in all 3 reasoning systems), eval run pending |
| Ablation (per-source Brier delta) | 🟡 Code done (`--disable-source` flag), 7-run sweep pending |
| Report quality (20-30 hand-scored on accuracy/completeness/reasoning/actionability) | ❌ NOT STARTED — needs reports from eval first |
| Secondary breakdowns (back-to-back, star absences, home/away) | 🟡 PARTIAL — B2B and home/away are derivable from existing columns; star absences need an extra slice query |

### Feasibility (proposal Section 6)

| Item | Proposal | Status |
|---|---|---|
| LLM cost | $50-100 | ✅ On track — using Haiku 4.5 (~$10 projected for full eval) |
| Compute | API + local ChromaDB | ✅ Working |
| Streamlit Cloud deployment | Free | 🟡 Pending — Tanish's task |

### Timeline (proposal Section 7)

Originally 4-week plan. Most of the build work landed today in one extended session. Remaining items: eval run (overnight), manual scoring (~5h split across team), report writing (per-member sections), Streamlit Cloud deploy.

### Innovation contributions (proposal Section 8)

| Contribution | Status |
|---|---|
| Structured vector store RAG with rich metadata | ✅ DONE |
| Multi-agent debate with differentiated analytical perspectives | ✅ DONE |
| Information density as a first-class variable | ✅ Infrastructure DONE, results pending |
| Deployed usable product | 🟡 Local works, cloud deploy pending (Tanish) |

---

## Part 2: What's left at a glance

| # | Task | Owner | Effort | Blocks |
|---|------|-------|--------|--------|
| 1 | Run full 150-game backtest (all 3 methods, Haiku) | **Aaditya** | ~14-17h wall, ~$10 | Most other tasks |
| 2 | Run 7 ablation sweeps on CoT (`--disable-source`) | **Aaditya** | ~2-3h, ~$2 | RQ3 results |
| 3 | Update RESULTS.md Section 5 with eval numbers | Pranav (auto via Claude) | ~30 min | Report writing |
| 4 | Manual report-quality scoring (20 reports, 4 criteria, 1-5 scale) | **All 3** (~7 reports each) | ~1.5h each | Report writing |
| 5 | Add Streamlit UI features per proposal | **Tanish** | ~5-8h | Demo |
| 6 | Deploy to Streamlit Cloud | **Tanish** | ~1h | Demo |
| 7 | Write report sections (per-member) | **All 3** | ~2-3h each | Final submission |
| 8 | (Optional polish) Add Bleacher Report RSS to news | Anyone | ~30 min | None |

---

# Part 3: Tanish — UI lane

## Plain-English brief

Hey Tanish — Pranav and his Claude Code finished all the backend work today. The agent system, data pipelines, vector store, and evaluation harness are all built and the data is populated. The Streamlit app **launches successfully** at `localhost:8501`. You can pick a game and run an analysis right now and it works.

**Your job is the UI/UX side that the proposal explicitly promises but isn't built yet.** Specifically:

1. **Decide which Streamlit file is canonical.** Two exist — `nba_streamlit_app.py` (original) and `Matchup_Analysis.py` (the 2067-line version you added). Diff them, pick one, delete the other. This is your call.

2. **Add three missing report sections per proposal:**
   - **Odds comparison across sportsbooks** — a table showing each bookmaker's moneyline + implied probability for the selected game. Data is already in `data/odds_live.csv`; the agent's `tool_get_odds()` returns it structured per bookmaker. You just need to render the table.
   - **Divergence flag** — when our AI's home_win_prob differs from market consensus by ≥5%, show a callout: "AI disagrees with market by X%" + brief reason from the agent's reasoning. The agent return shape will eventually have a `divergence` field; for now, compute it client-side from agent's prob vs market consensus.
   - **"Similar past games" section** — show the top 3-5 games the vector store retrieved, with metadata (back-to-back? home/away? rest days?) and outcome. Currently the agent uses these internally but the user never sees them.

3. **Add two missing eval-page features** (in `pages/Research_Evaluation.py`):
   - **Info density plots (RQ1 headline)** — scatter plot of info_density (any of the 4 signals: youtube_comments, news_articles, vector_hits, context_tokens) vs Brier score, segmented by game profile (high vs low info). Data lands in `data/backtest_predictions.csv` after Aaditya runs the eval.
   - **Ablation results section (RQ3)** — bar chart of per-source Brier delta. Reads `data/backtest_ablation_<source>.csv` files Aaditya generates.

4. **Caching + secrets:**
   - Wrap data loaders with `@st.cache_data` (TTL: 5 min for live odds, longer for static CSVs)
   - Create `.streamlit/secrets.toml` mirroring `.env` so the app reads keys via `st.secrets[...]` (gitignore the secrets file)

5. **Deploy to Streamlit Cloud.** Free at streamlit.io/cloud. Connect the GitHub repo, point it at the canonical Streamlit file, configure secrets in the Streamlit Cloud UI.

**Files you OWN:** `nba_streamlit_app.py`, `Matchup_Analysis.py`, `pages/Research_Evaluation.py`, `pages/Simulation_Betting_ROI.py`, anything new under `pages/`, `.streamlit/secrets.toml` (gitignored).

**Files you MUST NOT touch:** all `nba_*_pipeline.py`, `nba_vector_store.py`, `nba_agent.py`, `nba_multi_agent.py`, `nba_cot_baseline.py`, `nba_backtest.py`, `nba_cost_logger.py`, `requirements.txt` (Pranav's lane).

**Workflow:** branch off main per item, open PR, merge with `gh pr merge --rebase --delete-branch` (no branch protection). Pranav's commit style: imperative subject under 70 chars, body explains "previously / now". No AI attribution, no Co-Authored-By lines.

**Estimated time:** 5-8 hours total across all items. Eval visualizations (#3) wait until Aaditya's eval lands; everything else you can start now.

## Pastable Claude Code prompt for Tanish

```
Hey Claude — I'm Tanish Patel, working on a Columbia STAT GR5293 group project called MatchOdds AI with my teammates Pranav Jain and Aaditya Pai. Pranav and his Claude finished all the backend work today; now I'm taking the frontend. I need you to handle my queue.

## Project context
NBA pre-game betting analyst. User picks an upcoming game, system generates a structured report with odds, injuries, fan sentiment, similar past games from the vector store, and the AI's prediction. Three reasoning strategies run in parallel: single ReAct agent, multi-agent debate, and CoT baseline. Headline research finding: prediction quality vs info density per game.

- Repo: github.com/aaditya79/MatchOdds-AI (Aaditya is the owner)
- Local clone: cd to wherever you have it before doing anything
- My GitHub: tanishpatel0106
- Required reading at repo root: AUDIT.md (initial audit), RESULTS.md (system architecture + decisions + result placeholders), STATUS_AND_HANDOFF.md (this file's source — for full proposal-compliance breakdown)
- Original spec: proposal.pdf

## Repo state at handoff
Main has all backend PRs landed. Data is fully populated (run `ls data/` to see CSVs and the chroma_db/ directory). Streamlit app launches with `streamlit run nba_streamlit_app.py` and serves at localhost:8501.

NO branch protection on main — merge PRs with `gh pr merge <PR#> --rebase --delete-branch` directly without reviews.

## Your lane (only these files)
- nba_streamlit_app.py
- Matchup_Analysis.py
- pages/Research_Evaluation.py
- pages/Simulation_Betting_ROI.py
- Anything new under pages/
- .streamlit/secrets.toml (gitignored — for credentials)

## Files you must NOT touch
- All nba_*_pipeline.py files (Pranav's data layer)
- nba_vector_store.py
- nba_agent.py, nba_multi_agent.py, nba_cot_baseline.py, nba_backtest.py, nba_cost_logger.py (Pranav's agent/eval layer)
- requirements.txt (only Pranav adds backend deps; you may add Streamlit-only ones but flag in PR)

## Your queue (in priority order)

Each item = its own branch + its own PR. Branch naming: `tanish/<short-description>`. Pranav's commit style: imperative subject under 70 chars, body explains "previously / now". NO AI attribution, NO Co-Authored-By lines, NO "🤖 Generated with Claude Code" footer.

### Item 1 — Decide canonical Streamlit file (~15 min, MUST do first)
Two Streamlit entry points exist: `nba_streamlit_app.py` (original, ~1900 lines) and `Matchup_Analysis.py` (~2067 lines, you added this). Diff them: `diff nba_streamlit_app.py Matchup_Analysis.py | head -200`. Pick one, delete the other with `git rm`. Commit message: "Remove duplicate Streamlit entry point — <kept-file> is canonical".

### Item 2 — Add odds comparison + divergence flag (~2-3h)
Per the proposal, the report should compare odds across sportsbooks AND flag when the AI disagrees with market consensus.

In the chosen Streamlit file (from Item 1):
- Add a section "Odds across sportsbooks" with a table: rows = bookmakers, columns = home_odds, home_implied_prob, away_odds, away_implied_prob. Data comes from `tool_get_odds(home, away)` which returns structured bookmaker data. Highlight the best line per side.
- After the AI's prediction is rendered, compute `divergence = abs(agent_home_prob - market_consensus_home_prob)` where market_consensus is the average of bookmaker implied probabilities. If divergence >= 0.05, render an alert badge: "AI disagrees with market by {divergence*100:.0f}%" with a brief reason pulled from the agent's `reasoning` field.

Branch: `tanish/odds-compare-divergence`.

### Item 3 — Surface vector store retrievals (~1-2h)
Per the proposal, "Historical Similar Games" is a key section users should see. The agent calls `tool_search_similar_games` internally but users never see what was retrieved. Add a "Similar past games this prediction is based on" section showing the top 3-5 retrieved games with: matchup, date, key metadata (back-to-back? home/away? rest days?), and outcome (W/L for the team being analyzed).

Branch: `tanish/vector-retrieval-display`.

### Item 4 — Caching + secrets.toml (~1-2h)
- Wrap data loaders with `@st.cache_data` (TTL: 5 min for live odds, longer for static stats CSVs).
- Create `.streamlit/secrets.toml` with the same keys as `.env` (ANTHROPIC_API_KEY, ODDS_API_KEY, YOUTUBE_API_KEY).
- Update Streamlit-only code (your files) to read via `st.secrets[...]` when running inside Streamlit, falling back to `os.environ.get` otherwise.
- Add `.streamlit/secrets.toml` to .gitignore.

Branch: `tanish/cache-and-secrets`.

### Item 5 — BLOCKED until Aaditya runs eval — Info density plots on eval page (~2-3h)
In `pages/Research_Evaluation.py`, add the headline RQ1 plot: scatter of one info_density signal vs Brier score, segmented by game profile (top vs bottom quartile by `context_tokens` is a good profile split). Use matplotlib (already installed). Reads `data/backtest_predictions.csv` after Aaditya runs the eval.

Branch: `tanish/info-density-plot`.

### Item 6 — BLOCKED until Aaditya runs ablations — Ablation results section (~1-2h)
In `pages/Research_Evaluation.py`, add a section comparing per-source Brier deltas. Reads `data/backtest_ablation_*.csv` files Aaditya generates. Bar chart of "Brier impact when this source is disabled" per source.

Branch: `tanish/ablation-results`.

### Item 7 — Deploy to Streamlit Cloud (~1h, after Items 1-4 ship)
1. Go to share.streamlit.io and connect the GitHub repo
2. Point it at the canonical Streamlit file
3. Configure secrets in the Streamlit Cloud UI (paste contents of .streamlit/secrets.toml — but use Aaditya's API keys for production, NOT Pranav's)
4. Confirm the deployed URL works

## Workflow recipe (for every item)
```
git checkout main && git pull origin main
git checkout -b tanish/<item-name>
# ... make changes ...
git status
git diff
git add <specific files only — never `git add -A`>
git commit -m "<concise imperative subject>

<body explaining: previously X / now Y>"
git push -u origin tanish/<item-name>
gh pr create --title "<short>" --body "<summary, test plan>"
gh pr merge --rebase --delete-branch
git checkout main && git pull origin main
```

## Engineering principles
- Surgical changes — touch only what the item requires
- Test as you go — run the Streamlit app and click through the feature you're building
- If something doesn't match this brief, STOP and ask Pranav. Don't improvise on architecture
- No new abstractions for single-use code

## When you're done
Tell Pranav which items you completed, paste merged PR URLs, surface anything weird you encountered.

Start with Item 1 right now.
```

---

# Part 4: Aaditya — Eval + report sections lane

## Plain-English brief

Hey Aaditya — Pranav and his Claude finished all the backend work today. The agent system you originally drafted (single agent, multi-agent debate, CoT) is now wired into a real backtest with proper `as_of_date` filtering (no historical data leakage), info-density tracking, ablation infrastructure, and cost logging. **Two things are left for you:**

**1. Run the full evaluation.** Per the proposal, this is 150 historical games across all 3 reasoning methods, plus 7 ablation sweeps. Cost ~$10 on Claude Haiku 4.5 (which we settled on for cost — 4x cheaper than Sonnet, JSON-parse retry handles its occasional failures). Wall-clock time: ~14-17 hours, so kick it off and let it run overnight.

**2. Write your assigned report sections.** Per the proposal, you write the "Agent Architecture & Multi-Agent Debate" section and the "Evaluation Results" section. You have the deepest context on the agent code (you drafted the originals); Pranav's Claude added the iterative debate per Du et al., info density tracking, cost logging, and the as_of_date plumbing — all summarized in `RESULTS.md` Section 3.2-3.3 and Section 4.

**Setup needed on your machine (~30 min, one-time):**
1. `git clone https://github.com/aaditya79/MatchOdds-AI.git && cd MatchOdds-AI`
2. `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`
3. Set up Java for `nbainjuries` (it needs an arm64 JDK):
   - `brew install openjdk@18`
   - `export JAVA_HOME=/opt/homebrew/opt/openjdk@18/libexec/openjdk.jdk/Contents/Home`
   - Add the export to your shell profile so it persists
4. `cp .env.example .env` and fill in:
   - `ANTHROPIC_API_KEY` (your own — easier to track spend on your account)
   - `ODDS_API_KEY` (free at the-odds-api.com)
   - `YOUTUBE_API_KEY` (free at console.cloud.google.com)
5. Populate the data dir (~60 min, mostly nba_api rate limit waits):
   ```
   .venv/bin/python nba_data_pipeline.py     # ~30 min, pulls 9 seasons
   .venv/bin/python nba_vector_store.py      # ~10 min, builds ChromaDB (22,930 docs)
   .venv/bin/python nba_news_pipeline.py     # ~5 min
   .venv/bin/python nba_reddit_pipeline.py   # ~10 min, public JSON endpoint, no app needed
   .venv/bin/python nba_youtube_pipeline.py  # live games only — won't help backtest much
   .venv/bin/python nba_injury_pipeline.py   # ~1 min (Java required)
   .venv/bin/python nba_odds_pipeline.py     # ~30 sec live + Kaggle CSV (manual download from kaggle.com/datasets/erichqiu/nba-odds-and-scores → save to data/kaggle_odds.csv)
   ```

**Then run the eval (overnight, ~14-17 hours, ~$10):**
```
.venv/bin/python nba_backtest.py --n-games 150 --season 2024-25
```

**Then run the 7 ablations (~2-3 hours, ~$2):**
```
for src in youtube news odds injuries vector_store h2h stats; do
  .venv/bin/python nba_backtest.py --n-games 150 --season 2024-25 --disable-source "$src"
done
```

**Then commit the resulting CSVs back** (these aren't gitignored — they're the eval results we ship):
```
git add data/backtest_predictions.csv data/backtest_summary.csv data/backtest_calibration.csv data/backtest_ablation_*.csv data/backtest_run_metadata.json
git commit -m "Add full 150-game eval + 7 ablation results"
git push
```

**Your report sections** are in the proposal Section 6 work split:
- "Agent architecture, debate, and evaluation results sections"
- Read RESULTS.md for the full source material
- Use the actual numbers from your eval CSVs
- Likely 2-3 hours of writing per section

**Files you OWN if you need to edit anything:**
- `nba_agent.py`, `nba_multi_agent.py`, `nba_cot_baseline.py`, `nba_backtest.py`, `nba_cost_logger.py`

**Files you MUST NOT touch:**
- All `nba_*_pipeline.py` files (Pranav)
- `nba_vector_store.py` (Pranav)
- `nba_streamlit_app.py`, `Matchup_Analysis.py`, `pages/` (Tanish)

**Important — please don't force-push main.** Earlier today there was a force-push incident that wiped Pranav's work. Always pull before push, never `git push --force` to main. If your local main looks divergent, ask Pranav before reconciling.

## Pastable Claude Code prompt for Aaditya

```
Hey Claude — I'm Aaditya Pai, working on a Columbia STAT GR5293 group project called MatchOdds AI with my teammates Pranav Jain and Tanish Patel. Pranav and his Claude finished all the backend code work today; my job is to RUN THE FULL EVAL and then WRITE MY ASSIGNED REPORT SECTIONS. I need you to handle this end-to-end.

## Project context
NBA pre-game betting analyst. Three reasoning strategies (single ReAct agent, multi-agent debate, CoT baseline) over 150 historical games. Headline research questions: RQ1 (prediction quality vs info density), RQ2 (multi-agent vs CoT), RQ3 (which sources matter via ablation). Per the proposal I write the "Agent Architecture & Multi-Agent Debate" and "Evaluation Results" report sections.

- Repo: github.com/aaditya79/MatchOdds-AI (I'm the owner)
- Required reading at repo root: AUDIT.md, RESULTS.md (system architecture + decisions + methodology + result placeholders), STATUS_AND_HANDOFF.md (full proposal-compliance breakdown)
- Original spec: proposal.pdf
- My GitHub: aaditya79

## Phase A — Setup (one-time, ~60 min, mostly waits)

1. `git clone https://github.com/aaditya79/MatchOdds-AI.git && cd MatchOdds-AI`
2. `python3.12 -m venv .venv` (use Python 3.12 specifically)
3. `.venv/bin/pip install -r requirements.txt`
4. Install ARM64 Java for nbainjuries:
   `brew install openjdk@18`
   Add to shell profile: `export JAVA_HOME=/opt/homebrew/opt/openjdk@18/libexec/openjdk.jdk/Contents/Home`
5. Get API keys:
   - Anthropic: console.anthropic.com → use my own key (easier to track spend, ~$10 expected for full eval)
   - The Odds API: free at the-odds-api.com
   - YouTube Data API v3: free at console.cloud.google.com → enable "YouTube Data API v3" → create API key
6. `cp .env.example .env` and paste keys
7. Manually download Kaggle dataset: kaggle.com/datasets/erichqiu/nba-odds-and-scores → save to `data/kaggle_odds.csv`
8. Verify setup: `.venv/bin/python -c "import anthropic, pandas, chromadb; print('ok')"` — if this hangs more than 30 sec, the macOS amfid issue Pranav documented is happening; recreate the venv: `rm -rf .venv && python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`

## Phase B — Populate data (~60 min, mostly nba_api rate limits)

Run these in order, each in foreground so failures surface:
```
set -a && source .env && set +a
.venv/bin/python nba_data_pipeline.py
.venv/bin/python nba_vector_store.py
.venv/bin/python nba_news_pipeline.py
.venv/bin/python nba_reddit_pipeline.py
.venv/bin/python nba_injury_pipeline.py
.venv/bin/python nba_odds_pipeline.py
```

Verify outputs in data/: game_logs.csv (>3MB), team_sentiment.csv, reddit_team_sentiment.csv, injuries.csv, odds_live.csv, odds_historical.csv. Plus chroma_db/ directory (built by vector store).

## Phase C — Smoke test (~5 min, ~$0.30)

Before the long run, sanity-check end-to-end:
```
.venv/bin/python nba_backtest.py --n-games 5 --season 2024-25
```

Watch the output for:
- 5 games selected
- Each game logs `single_agent`, `chain_of_thought`, `multi_agent_debate` results
- Occasional `parse failed (attempt N/3), retrying` is normal — that's the JSON parse retry working
- Cost log at `data/llm_calls.jsonl` populating

If the smoke fails or takes >1 hour, stop and message Pranav.

## Phase D — Full eval (overnight, ~14-17h, ~$10)

```
.venv/bin/python nba_backtest.py --n-games 150 --season 2024-25
```

Run in `nohup ... &` or `tmux` so it survives shell disconnect. Monitor with:
```
tail -f /tmp/eval.log  # if you redirected
.venv/bin/python -c "import json; calls = [json.loads(l) for l in open('data/llm_calls.jsonl')]; print(f'{len(calls)} calls, \${sum(c[\"cost_usd\"] for c in calls):.2f}')"
```

When done, expected outputs in data/:
- backtest_predictions.csv (150 rows × 3 methods = 450 prediction rows)
- backtest_summary.csv (per-method aggregate metrics)
- backtest_calibration.csv (calibration curve data)
- backtest_run_metadata.json

## Phase E — Ablation sweeps (~2-3h, ~$2)

```
for src in youtube news odds injuries vector_store h2h stats; do
  .venv/bin/python nba_backtest.py --n-games 150 --season 2024-25 --disable-source "$src"
done
```

Each run produces `data/backtest_ablation_<source>.csv`.

## Phase F — Commit results

```
git checkout -b aaditya/eval-results
git add data/backtest_*.csv data/backtest_run_metadata.json data/llm_calls.jsonl
git commit -m "Add full 150-game eval + 7 ablation results

Sample: 150 games from 2024-25 season, all 3 reasoning methods.
Model: Claude Haiku 4.5. Total cost: \$X.XX (verified from llm_calls.jsonl).
Ablations: 7 single-source disables on CoT baseline."
git push -u origin aaditya/eval-results
gh pr create --title "Eval results: 150-game backtest + 7 ablations"
gh pr merge --merge --delete-branch
```

## Phase G — Update RESULTS.md with real numbers (~1h)

Open `RESULTS.md`. Section 5 has placeholders ("_TBD_") for:
- 5.1 Cost & resource usage
- 5.2 Main comparison: single vs CoT vs multi-agent (RQ2)
- 5.3 Information density vs prediction quality (RQ1)
- 5.4 Ablation: per-source impact (RQ3)
- 5.6 Calibration
- 5.7 Secondary breakdowns

Fill them from the eval CSVs you just generated. Use pandas to compute:
- Brier, log loss, ECE per method (already in backtest_summary.csv)
- Pearson/Spearman correlation: info_density columns vs Brier (compute from backtest_predictions.csv)
- Per-source Brier delta (from backtest_ablation_*.csv vs backtest_predictions.csv baseline)

Commit + PR + merge.

## Phase H — Write your report sections (~5h)

Per proposal Section 6, you write:
- "Agent architecture, debate, and evaluation results sections"

Use RESULTS.md as the source-of-truth content (system architecture in Section 2, methodology in Section 4, your numbers in Section 5). Translate to formal academic prose. Reference the proposal for framing.

Save to `report/aaditya_sections.md` (or wherever the team is collecting report drafts).

## Files you OWN
- nba_agent.py
- nba_multi_agent.py
- nba_cot_baseline.py
- nba_backtest.py
- nba_cost_logger.py
- data/backtest_*.csv (you generate these)

## Files you MUST NOT touch
- All nba_*_pipeline.py files (Pranav)
- nba_vector_store.py (Pranav)
- nba_streamlit_app.py, Matchup_Analysis.py, pages/ (Tanish)
- .env (your own copy is fine, but don't commit it — it's gitignored)

## Critical: do NOT force-push main
Earlier today there was an incident where main got force-pushed and lost work. Always `git pull` before pushing. Never `git push --force` to main. If your local main looks divergent, message Pranav before reconciling.

## Report back
After each Phase (smoke success, eval done, ablations done, RESULTS.md updated, sections written), tell Pranav: what completed, any errors, the merged PR URL. Surface anything weird.

Start with Phase A right now.
```

---

## Document maintenance

This file gets updated whenever:
- A team member completes their queue
- A new gap is found
- The proposal compliance map changes

If you're reading this and something here is wrong or out of date, fix it and commit.
