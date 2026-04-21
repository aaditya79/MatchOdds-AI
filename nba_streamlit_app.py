import os
import json
import streamlit as st
import pandas as pd
from datetime import datetime

from nba_agent import (
    tool_get_team_stats,
    tool_get_head_to_head,
    tool_get_injuries,
    tool_get_odds,
    tool_search_similar_games,
    run_agent,
)
from nba_multi_agent import run_full_debate, AGENTS
from nba_cot_baseline import run_cot_analysis


TEAMS = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "LA Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}

TEAM_LOGOS = {
    "ATL": "https://a.espncdn.com/i/teamlogos/nba/500/atl.png",
    "BOS": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png",
    "BKN": "https://a.espncdn.com/i/teamlogos/nba/500/bkn.png",
    "CHA": "https://a.espncdn.com/i/teamlogos/nba/500/cha.png",
    "CHI": "https://a.espncdn.com/i/teamlogos/nba/500/chi.png",
    "CLE": "https://a.espncdn.com/i/teamlogos/nba/500/cle.png",
    "DAL": "https://a.espncdn.com/i/teamlogos/nba/500/dal.png",
    "DEN": "https://a.espncdn.com/i/teamlogos/nba/500/den.png",
    "DET": "https://a.espncdn.com/i/teamlogos/nba/500/det.png",
    "GSW": "https://a.espncdn.com/i/teamlogos/nba/500/gsw.png",
    "HOU": "https://a.espncdn.com/i/teamlogos/nba/500/hou.png",
    "IND": "https://a.espncdn.com/i/teamlogos/nba/500/ind.png",
    "LAC": "https://a.espncdn.com/i/teamlogos/nba/500/lac.png",
    "LAL": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png",
    "MEM": "https://a.espncdn.com/i/teamlogos/nba/500/mem.png",
    "MIA": "https://a.espncdn.com/i/teamlogos/nba/500/mia.png",
    "MIL": "https://a.espncdn.com/i/teamlogos/nba/500/mil.png",
    "MIN": "https://a.espncdn.com/i/teamlogos/nba/500/min.png",
    "NOP": "https://a.espncdn.com/i/teamlogos/nba/500/no.png",
    "NYK": "https://a.espncdn.com/i/teamlogos/nba/500/ny.png",
    "OKC": "https://a.espncdn.com/i/teamlogos/nba/500/okc.png",
    "ORL": "https://a.espncdn.com/i/teamlogos/nba/500/orl.png",
    "PHI": "https://a.espncdn.com/i/teamlogos/nba/500/phi.png",
    "PHX": "https://a.espncdn.com/i/teamlogos/nba/500/phx.png",
    "POR": "https://a.espncdn.com/i/teamlogos/nba/500/por.png",
    "SAC": "https://a.espncdn.com/i/teamlogos/nba/500/sac.png",
    "SAS": "https://a.espncdn.com/i/teamlogos/nba/500/sas.png",
    "TOR": "https://a.espncdn.com/i/teamlogos/nba/500/tor.png",
    "UTA": "https://a.espncdn.com/i/teamlogos/nba/500/uta.png",
    "WAS": "https://a.espncdn.com/i/teamlogos/nba/500/wsh.png",
}


CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #336b95;
        --panel: rgba(255,255,255,0.12);
        --panel-strong: rgba(255,255,255,0.16);
        --card: rgba(255,255,255,0.10);
        --card-2: rgba(255,255,255,0.14);
        --border: rgba(255,255,255,0.16);
        --text: #f7fbff;
        --muted: rgba(247,251,255,0.76);
        --soft: rgba(247,251,255,0.56);
        --green: #39d98a;
        --red: #ff6b6b;
        --yellow: #ffd166;
        --blue: #8bc1ff;
        --shadow: 0 10px 30px rgba(10, 28, 45, 0.22);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.07), transparent 24%),
            radial-gradient(circle at top right, rgba(255,255,255,0.05), transparent 20%),
            linear-gradient(180deg, #3f79a7 0%, #336b95 48%, #2d628b 100%);
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }

    .block-container {
        max-width: 1280px;
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }

    #MainMenu, header, footer {
        visibility: hidden;
    }

    .top-banner {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.14);
        color: var(--text);
        border-radius: 18px;
        padding: 12px 16px;
        margin-bottom: 18px;
        font-size: 0.92rem;
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px);
    }

    .hero {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 18px;
        margin-bottom: 20px;
    }

    .hero-left h1 {
        margin: 0;
        font-size: 2.3rem;
        line-height: 1.05;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.03em;
    }

    .hero-left p {
        margin: 8px 0 0 0;
        color: var(--muted);
        font-size: 1rem;
    }

    .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border-radius: 999px;
        padding: 10px 14px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.14);
        color: var(--text);
        font-size: 0.86rem;
        font-weight: 600;
        white-space: nowrap;
        box-shadow: var(--shadow);
    }

    .glass-card {
        background: rgba(20, 45, 66, 0.18);
        border: 1px solid rgba(255,255,255,0.14);
        border-radius: 22px;
        padding: 18px 18px 16px 18px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
        margin-bottom: 16px;
    }

    .section-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: var(--text);
        margin-bottom: 12px;
    }

    .subtle {
        color: var(--muted);
        font-size: 0.92rem;
    }

    .method-card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
        padding: 14px;
        height: 100%;
    }

    .method-title {
        font-weight: 700;
        margin-bottom: 6px;
        color: var(--text);
    }

    .method-copy {
        color: var(--muted);
        font-size: 0.88rem;
        line-height: 1.55;
    }

    .score-card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 20px;
        padding: 16px;
        text-align: center;
    }

    .score-label {
        color: var(--soft);
        text-transform: uppercase;
        font-size: 0.74rem;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
        font-weight: 700;
    }

    .score-value {
        color: var(--text);
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }

    .score-value.green { color: var(--green); }
    .score-value.red { color: var(--red); }
    .score-value.blue { color: var(--blue); }

    .metric-chip {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }

    .metric-chip .k {
        color: var(--soft);
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .metric-chip .v {
        color: var(--text);
        font-size: 1.12rem;
        font-weight: 700;
    }

    .team-block {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .team-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text);
    }

    .team-abbr {
        font-size: 0.86rem;
        color: var(--muted);
        font-weight: 600;
    }

    .vs-text {
        color: var(--soft);
        font-size: 1.1rem;
        font-weight: 800;
    }

    .ring-card {
        flex: 1;
        min-width: 220px;
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.11);
        border-radius: 20px;
        padding: 18px;
        text-align: center;
    }

    .ring {
        width: 130px;
        height: 130px;
        border-radius: 50%;
        margin: 0 auto 10px auto;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }

    .ring::before {
        content: "";
        width: 92px;
        height: 92px;
        background: rgba(36, 64, 88, 0.98);
        border-radius: 50%;
        position: absolute;
    }

    .ring-inner {
        position: relative;
        z-index: 1;
        text-align: center;
    }

    .ring-pct {
        font-size: 1.9rem;
        font-weight: 800;
        line-height: 1;
    }

    .ring-team {
        font-size: 0.82rem;
        color: var(--muted);
        margin-top: 6px;
        font-weight: 600;
    }

    .factor-box {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.11);
        border-radius: 18px;
        padding: 14px;
        height: 100%;
    }

    .factor-top {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 8px;
        align-items: center;
    }

    .factor-badge {
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .factor-home { background: rgba(57,217,138,0.18); color: #98f0be; }
    .factor-away { background: rgba(255,107,107,0.18); color: #ffb1b1; }
    .factor-neutral { background: rgba(139,193,255,0.18); color: #cbe3ff; }

    .factor-importance {
        color: var(--soft);
        font-size: 0.75rem;
        text-transform: uppercase;
        font-weight: 700;
    }

    .factor-text {
        color: var(--text);
        font-size: 0.94rem;
        line-height: 1.55;
    }

    .bar-wrap {
        margin-top: 10px;
    }

    .bar-label {
        display: flex;
        justify-content: space-between;
        color: var(--muted);
        font-size: 0.84rem;
        margin-bottom: 6px;
    }

    .bar {
        width: 100%;
        height: 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.10);
        overflow: hidden;
    }

    .bar-fill-green {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #39d98a, #9cf1c0);
    }

    .bar-fill-red {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #ff8e8e, #ff6b6b);
    }

    .text-panel {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.11);
        border-radius: 18px;
        padding: 16px;
        color: var(--text);
        line-height: 1.7;
        font-size: 0.95rem;
    }

    .verdict-card {
        background: linear-gradient(135deg, rgba(57,217,138,0.15), rgba(139,193,255,0.11));
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 22px;
        padding: 18px;
        box-shadow: var(--shadow);
    }

    .verdict-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--soft);
        font-weight: 800;
        margin-bottom: 8px;
    }

    .verdict-main {
        font-size: 1.45rem;
        font-weight: 800;
        color: var(--text);
        line-height: 1.25;
        margin-bottom: 8px;
    }

    .verdict-sub {
        color: var(--muted);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    .footer-note {
        color: rgba(247,251,255,0.65);
        text-align: center;
        font-size: 0.82rem;
        margin-top: 24px;
    }

    .stButton > button {
        border-radius: 14px;
        border: 0;
        background: linear-gradient(135deg, #9ec8ff, #71afff);
        color: #0b2337;
        font-weight: 800;
        padding: 0.72rem 1.25rem;
        box-shadow: var(--shadow);
    }

    .stDownloadButton > button {
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.12);
        color: white;
        font-weight: 700;
    }

    .stRadio > div {
        background: transparent;
        padding: 0;
        border: none;
    }

    div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
        border-radius: 14px !important;
        color: white !important;
    }

    .stDateInput > div > div {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.16) !important;
        border-radius: 14px !important;
    }

    .stDateInput input {
        color: white !important;
        background: transparent !important;
    }

    .stTextInput input,
    input {
        color: white !important;
    }

    label, .stDateInput label, .stSelectbox label {
        color: var(--muted) !important;
        font-weight: 600 !important;
    }

    hr {
        display: none !important;
    }
</style>
"""


def get_llm_fn():
    if os.environ.get("ANTHROPIC_API_KEY"):
        def call_anthropic(messages):
            import anthropic
            client = anthropic.Anthropic()
            system_msg = ""
            conv_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    conv_messages.append(msg)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_msg if system_msg else "You are an NBA betting analyst.",
                messages=conv_messages,
            )
            return response.content[0].text
        return call_anthropic, "Claude"
    elif os.environ.get("OPENAI_API_KEY"):
        def call_openai(messages):
            from openai import OpenAI
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=4096
            )
            return response.choices[0].message.content
        return call_openai, "GPT-4o"
    return None, None


def parse_report(report_text):
    if "FINAL REPORT:" in report_text:
        json_str = report_text.split("FINAL REPORT:")[-1].strip()
    else:
        json_str = report_text.strip()
    try:
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(json_str[start:end])
    except json.JSONDecodeError:
        pass
    return None


def safe_load_json(raw, default=None):
    try:
        return json.loads(raw)
    except:
        return default if default is not None else {}


def pct_str(x):
    if isinstance(x, (int, float)):
        return f"{x:.0%}"
    return str(x)


def get_prediction_block(report_json):
    pred = report_json.get("prediction") or report_json.get("synthesized_prediction") or report_json.get("agent_prediction", {})
    home_prob = pred.get("home_win_prob", 0.5)
    away_prob = pred.get("away_win_prob", 0.5)
    confidence = pred.get("confidence", "Medium")
    return pred, home_prob, away_prob, confidence


def render_header(llm_name):
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="top-banner">
            <strong>Research purposes only.</strong> MatchOdds AI is an experimental game analysis interface for studying matchup edges, team context, injuries, and pricing signals. It is <strong>not financial advice</strong>.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-left">
                <h1>MatchOdds AI</h1>
                <p>NBA matchup analysis with cleaner reasoning, clearer metrics, and side-by-side model views.</p>
            </div>
            <div class="hero-pill">Model Engine: {llm_name}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_method_guide():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Analysis Types</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="method-card">
                <div class="method-title">Multi-Agent Debate</div>
                <div class="method-copy">
                    Best for deeper analysis. Multiple specialized agents challenge each other before a final synthesis. More robust, slower, and usually the most complete.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            """
            <div class="method-card">
                <div class="method-title">Single Agent</div>
                <div class="method-copy">
                    One analyst pulls evidence and produces a direct recommendation. Faster and simpler, with less cross-checking than the debate mode.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            """
            <div class="method-card">
                <div class="method-title">Chain-of-Thought</div>
                <div class="method-copy">
                    Most transparent linear reasoning path. Good when you want to inspect the logic step by step without multiple agent disagreement layers.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)


def render_matchup_header(home_team, away_team, home_abbr, away_abbr, game_date):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Matchup</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3, 1, 3])
    with c1:
        st.markdown(
            f"""
            <div class="team-block">
                <img src="{TEAM_LOGOS.get(away_abbr, '')}" width="52">
                <div>
                    <div class="team-name">{away_team}</div>
                    <div class="team-abbr">Away · {away_abbr}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown('<div style="text-align:center; padding-top:12px;" class="vs-text">@</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(
            f"""
            <div class="team-block" style="justify-content:flex-end;">
                <div style="text-align:right;">
                    <div class="team-name">{home_team}</div>
                    <div class="team-abbr">Home · {home_abbr}</div>
                </div>
                <img src="{TEAM_LOGOS.get(home_abbr, '')}" width="52">
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div style="margin-top:14px;" class="subtle">
            Game date: <strong>{game_date.strftime('%A, %B %d, %Y')}</strong>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


def render_team_snapshot(home_team, away_team, home_abbr, away_abbr):
    home_stats = safe_load_json(tool_get_team_stats(home_abbr), {})
    away_stats = safe_load_json(tool_get_team_stats(away_abbr), {})

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Team Snapshot</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    def render_metric(label, value):
        st.markdown(
            f"""
            <div class="metric-chip">
                <div class="k">{label}</div>
                <div class="v">{value}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col1:
        st.markdown(f"#### {home_team}")

        pm = home_stats.get("avg_plus_minus_last_10", "N/A")
        fg = home_stats.get("avg_fg_pct_last_10", None)

        pm_text = f"{pm:+.1f}" if isinstance(pm, (int, float)) else str(pm)
        fg_text = f"{fg:.1%}" if isinstance(fg, (int, float)) else "N/A"

        render_metric("Season Record", home_stats.get("season_record", "N/A"))
        render_metric("Last 10", home_stats.get("last_10_record", "N/A"))
        render_metric("Avg Pts Last 10", home_stats.get("avg_points_last_10", "N/A"))
        render_metric("Avg +/- Last 10", pm_text)
        render_metric("FG% Last 10", fg_text)

    with col2:
        st.markdown(f"#### {away_team}")

        pm = away_stats.get("avg_plus_minus_last_10", "N/A")
        fg = away_stats.get("avg_fg_pct_last_10", None)

        pm_text = f"{pm:+.1f}" if isinstance(pm, (int, float)) else str(pm)
        fg_text = f"{fg:.1%}" if isinstance(fg, (int, float)) else "N/A"

        render_metric("Season Record", away_stats.get("season_record", "N/A"))
        render_metric("Last 10", away_stats.get("last_10_record", "N/A"))
        render_metric("Avg Pts Last 10", away_stats.get("avg_points_last_10", "N/A"))
        render_metric("Avg +/- Last 10", pm_text)
        render_metric("FG% Last 10", fg_text)

    st.markdown('</div>', unsafe_allow_html=True)


def render_injury_summary(home_team, away_team):
    home_inj = safe_load_json(tool_get_injuries(home_team), [])
    away_inj = safe_load_json(tool_get_injuries(away_team), [])

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Injury & Availability</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    def team_inj(col, team_name, injuries):
        with col:
            st.markdown(f"#### {team_name}")
            if not injuries:
                st.markdown('<div class="text-panel">No reported injuries.</div>', unsafe_allow_html=True)
                return
            rows = []
            for inj in injuries[:8]:
                status = inj.get("status", "Unknown")
                player = inj.get("player", "Unknown")
                pos = inj.get("position", "")
                comment = str(inj.get("comment", ""))[:110]
                color = "#ff6b6b" if status.lower() == "out" else "#ffd166"
                rows.append(
                    f"<div style='margin-bottom:10px;'><strong style='color:{color};'>{status}</strong> · {player} <span style='color:rgba(247,251,255,0.7);'>({pos})</span><br><span style='color:rgba(247,251,255,0.72); font-size:0.88rem;'>{comment}</span></div>"
                )
            st.markdown(f"<div class='text-panel'>{''.join(rows)}</div>", unsafe_allow_html=True)

    team_inj(c1, home_team, home_inj)
    team_inj(c2, away_team, away_inj)
    st.markdown('</div>', unsafe_allow_html=True)


def render_prediction_visuals(report_json, home_team, away_team):
    _, home_prob, away_prob, confidence = get_prediction_block(report_json)
    home_pct = int(round((home_prob if isinstance(home_prob, (int, float)) else 0.5) * 100))
    away_pct = int(round((away_prob if isinstance(away_prob, (int, float)) else 0.5) * 100))
    conf_map = {"low": 36, "medium": 62, "high": 82}
    conf_score = conf_map.get(str(confidence).lower(), 62)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Win Probability</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 2, 1.5])

    with c1:
        st.markdown(
            f"""
            <div class="ring-card">
                <div class="score-label">{home_team} Win</div>
                <div class="ring" style="background: conic-gradient(#35d07f 0% {home_pct}%, rgba(255,255,255,0.10) {home_pct}% 100%);">
                    <div class="ring-inner">
                        <div class="ring-pct" style="color:#87f2b5;">{home_pct}%</div>
                        <div class="ring-team">Home</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="ring-card">
                <div class="score-label">{away_team} Win</div>
                <div class="ring" style="background: conic-gradient(#ff6b6b 0% {away_pct}%, rgba(255,255,255,0.10) {away_pct}% 100%);">
                    <div class="ring-inner">
                        <div class="ring-pct" style="color:#ffb3b3;">{away_pct}%</div>
                        <div class="ring-team">Away</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:
        conf_label = str(confidence).capitalize()
        edge = abs(home_pct - away_pct)
        st.markdown(
            f"""
            <div class="score-card">
                <div class="score-label">Confidence</div>
                <div class="score-value blue">{conf_label}</div>
                <div class="bar-wrap">
                    <div class="bar-label"><span>Model confidence</span><span>{conf_score}/100</span></div>
                    <div class="bar"><div class="bar-fill-green" style="width:{conf_score}%;"></div></div>
                </div>
                <div class="bar-wrap">
                    <div class="bar-label"><span>Prediction gap</span><span>{edge} pts</span></div>
                    <div class="bar"><div class="bar-fill-red" style="width:{min(edge,100)}%;"></div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)


def render_key_factors(factors):
    if not factors:
        return

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Key Factors</div>', unsafe_allow_html=True)

    cols = st.columns(2)
    for i, f in enumerate(factors):
        impact = str(f.get("impact", "neutral")).lower()
        importance = f.get("importance", "medium").upper()
        text = f.get("factor", "")

        if "home" in impact or "favors home" in impact or "positive" in impact:
            badge_class = "factor-home"
            badge_text = "Home Edge"
        elif "away" in impact or "favors away" in impact or "negative" in impact:
            badge_class = "factor-away"
            badge_text = "Away Edge"
        else:
            badge_class = "factor-neutral"
            badge_text = "Neutral"

        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="factor-box">
                    <div class="factor-top">
                        <span class="factor-badge {badge_class}">{badge_text}</span>
                        <span class="factor-importance">{importance}</span>
                    </div>
                    <div class="factor-text">{text}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)


def render_reasoning_value(report_json):
    reasoning = report_json.get("reasoning", "")
    value = report_json.get("value_assessment", "")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="glass-card"><div class="section-title">Reasoning</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="text-panel">{reasoning if reasoning else "No reasoning provided."}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass-card"><div class="section-title">Value Assessment</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="text-panel">{value if value else "No value commentary provided."}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_agent_breakdown(agent_analyses):
    if not agent_analyses:
        return

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Agent Breakdown</div>', unsafe_allow_html=True)

    cols = st.columns(len(agent_analyses))
    for i, (agent_key, analysis) in enumerate(agent_analyses.items()):
        name = AGENTS[agent_key]["name"].replace(" Agent", "")
        pred = analysis.get("prediction", {})
        home = pred.get("home_win_prob", 0.5)
        away = pred.get("away_win_prob", 0.5)
        conf = analysis.get("confidence", "Medium")

        with cols[i]:
            st.markdown(
                f"""
                <div class="score-card">
                    <div class="score-label">{name}</div>
                    <div class="subtle" style="margin-bottom:10px;">Home {pct_str(home)} · Away {pct_str(away)}</div>
                    <div class="bar-wrap">
                        <div class="bar-label"><span>Home lean</span><span>{pct_str(home)}</span></div>
                        <div class="bar"><div class="bar-fill-green" style="width:{int((home if isinstance(home,(int,float)) else 0.5)*100)}%;"></div></div>
                    </div>
                    <div class="bar-wrap">
                        <div class="bar-label"><span>Confidence</span><span>{conf}</span></div>
                        <div class="bar"><div class="bar-fill-red" style="width:{82 if str(conf).lower()=='high' else 62 if str(conf).lower()=='medium' else 38}%;"></div></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    st.markdown('</div>', unsafe_allow_html=True)


def render_agreement(report_json):
    agree = report_json.get("areas_of_agreement", [])
    disagree = report_json.get("areas_of_disagreement", [])

    if not agree and not disagree:
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="glass-card"><div class="section-title">Areas of Agreement</div>', unsafe_allow_html=True)
        if agree:
            st.markdown(
                "<div class='text-panel'>" + "".join([f"• {x}<br>" for x in agree]) + "</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown("<div class='text-panel'>No clear agreement items.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="glass-card"><div class="section-title">Areas of Disagreement</div>', unsafe_allow_html=True)
        if disagree:
            st.markdown(
                "<div class='text-panel'>" + "".join([f"• {x}<br>" for x in disagree]) + "</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown("<div class='text-panel'>No major disagreement items.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def render_final_prediction(report_json, home_team, away_team):
    _, home_prob, away_prob, confidence = get_prediction_block(report_json)

    winner = home_team if home_prob >= away_prob else away_team
    edge = abs(home_prob - away_prob) if isinstance(home_prob, (int, float)) and isinstance(away_prob, (int, float)) else 0

    summary = report_json.get("value_assessment") or report_json.get("reasoning") or ""
    if len(summary) > 240:
        summary = summary[:240].rsplit(" ", 1)[0] + "..."

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="verdict-card">
            <div class="verdict-title">Final Prediction</div>
            <div class="verdict-main">{winner} projected to win</div>
            <div class="verdict-sub">
                Estimated confidence: <strong>{str(confidence).capitalize()}</strong> · 
                model gap: <strong>{edge:.1%}</strong><br><br>
                {summary}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)


def build_download_payload(mode, game_description, result, report_json):
    payload = {
        "product": "MatchOdds AI",
        "mode": mode,
        "game": game_description,
        "generated_at": datetime.utcnow().isoformat(),
        "summary_report": report_json,
        "full_result": result,
    }
    return json.dumps(payload, indent=2)


def main():
    st.set_page_config(page_title="MatchOdds AI", page_icon="🏀", layout="wide")

    llm_fn, llm_name = get_llm_fn()
    if not llm_fn:
        st.error("No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY before running.")
        st.stop()

    render_header(llm_name)
    render_method_guide()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Select Game</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3, 3, 2])
    with c1:
        away_team = st.selectbox("Away Team", list(TEAMS.keys()), index=list(TEAMS.keys()).index("Boston Celtics"))
    with c2:
        home_team = st.selectbox("Home Team", list(TEAMS.keys()), index=list(TEAMS.keys()).index("Brooklyn Nets"))
    with c3:
        game_date_text = st.text_input("Date", value=datetime.now().strftime("%Y-%m-%d"))
    try:
        game_date = datetime.strptime(game_date_text, "%Y-%m-%d")
    except ValueError:
        st.error("Please enter the date as YYYY-MM-DD.")
        st.stop()

    mode = st.radio(
        "Analysis Mode",
        ["Multi-Agent Debate", "Single Agent", "Chain-of-Thought"],
        horizontal=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)

    if home_team == away_team:
        st.warning("Select two different teams.")
        st.stop()

    home_abbr = TEAMS[home_team]
    away_abbr = TEAMS[away_team]
    game_description = f"{away_team} vs {home_team}, {game_date.strftime('%B %d, %Y')}"

    render_matchup_header(home_team, away_team, home_abbr, away_abbr, game_date)
    render_team_snapshot(home_team, away_team, home_abbr, away_abbr)
    render_injury_summary(home_team, away_team)

    if st.button("Run Analysis"):
        with st.spinner(f"Running {mode}..."):
            result = None
            report_json = None

            if mode == "Single Agent":
                result = run_agent(game_description, llm_fn)
                report_json = parse_report(result["final_response"])

            elif mode == "Chain-of-Thought":
                result = run_cot_analysis(home_abbr, away_abbr, home_team, away_team, game_description, llm_fn)
                report_json = parse_report(result["response"])

            elif mode == "Multi-Agent Debate":
                result = run_full_debate(game_description, llm_fn, num_debate_rounds=2)
                report_json = parse_report(result["final_report"])

            if report_json:
                render_prediction_visuals(report_json, home_team, away_team)
                render_key_factors(report_json.get("key_factors", []))

                if mode == "Multi-Agent Debate":
                    render_agent_breakdown(result.get("agent_analyses", {}))
                    render_agreement(report_json)

                render_reasoning_value(report_json)
                render_final_prediction(report_json, home_team, away_team)

                download_text = build_download_payload(mode, game_description, result, report_json)
                st.download_button(
                    label="Download Full Report",
                    data=download_text,
                    file_name=f"matchodds_report_{away_abbr}_at_{home_abbr}_{game_date.strftime('%Y%m%d')}.json",
                    mime="application/json"
                )

                with st.expander("View Full Structured Output"):
                    st.json(report_json)

                with st.expander("View Full Raw Analysis"):
                    st.json(result)

            else:
                st.error("Could not parse a structured report from the model output.")
                st.write(result)

    st.markdown(
        """
        <div class="footer-note">
            MatchOdds AI · Research interface only · Not financial advice
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()