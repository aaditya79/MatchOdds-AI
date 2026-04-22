"""
Step 9: Chain-of-Thought Baseline
A single agent that receives ALL gathered evidence at once and reasons
through it in one pass. No tool calling, no iterative gathering.

This is the baseline to compare against the multi-agent debate (Step 8).
The question: does structured multi-agent disagreement outperform a
single generalist thinking carefully with the same data?

Usage:
    export ANTHROPIC_API_KEY="your_key"   (or OPENAI_API_KEY)
    python nba_cot_baseline.py

Requires: steps 1-3 and 5 completed (data/ populated)
"""

import os
import json
from datetime import datetime

from nba_agent import (
    tool_get_team_stats,
    tool_get_head_to_head,
    tool_get_injuries,
    tool_get_odds,
    tool_search_similar_games,
    tool_get_team_sentiment,
    DATA_DIR,
)


# ============================================================
# PRE-GATHER ALL EVIDENCE
# ============================================================

def gather_all_evidence(home_team_abbr, away_team_abbr, home_team_name, away_team_name):
    """
    Gather all available data upfront. No agent decision-making here.
    Just pull everything and hand it to the LLM in one shot.
    """
    print("Gathering all evidence upfront...")
    evidence = {}

    print(f"  Getting {home_team_abbr} stats...")
    evidence["home_team_stats"] = tool_get_team_stats(home_team_abbr)

    print(f"  Getting {away_team_abbr} stats...")
    evidence["away_team_stats"] = tool_get_team_stats(away_team_abbr)

    print(f"  Getting H2H record...")
    evidence["head_to_head"] = tool_get_head_to_head(home_team_abbr, away_team_abbr)

    print(f"  Getting {home_team_name} injuries...")
    evidence["home_injuries"] = tool_get_injuries(home_team_name)

    print(f"  Getting {away_team_name} injuries...")
    evidence["away_injuries"] = tool_get_injuries(away_team_name)

    print(f"  Getting {home_team_abbr} sentiment...")
    evidence["home_team_sentiment"] = tool_get_team_sentiment(home_team_abbr)

    print(f"  Getting {away_team_abbr} sentiment...")
    evidence["away_team_sentiment"] = tool_get_team_sentiment(away_team_abbr)

    print(f"  Getting odds...")
    evidence["odds"] = tool_get_odds(home_team_name, away_team_name)

    print(f"  Searching similar games for {home_team_abbr}...")
    evidence["similar_home"] = tool_search_similar_games(
        f"{home_team_abbr} home game recent form",
        team=home_team_abbr,
        n_results=3
    )

    print(f"  Searching similar games for {away_team_abbr}...")
    evidence["similar_away"] = tool_search_similar_games(
        f"{away_team_abbr} away game recent form",
        team=away_team_abbr,
        n_results=3
    )

    total_chars = sum(len(str(v)) for v in evidence.values())
    evidence["_info_density"] = {
        "total_characters": total_chars,
        "sources_with_data": sum(
            1 for v in evidence.values()
            if v and str(v) != "[]" and "No " not in str(v)[:20]
        ),
        "total_sources_queried": len(evidence),
    }

    print(
        f"  Total evidence: {total_chars} characters from "
        f"{evidence['_info_density']['sources_with_data']} sources"
    )
    return evidence


# ============================================================
# COT PROMPT
# ============================================================

def build_cot_prompt(game_description, evidence):
    """Build a single prompt with all evidence for one-pass reasoning."""

    return f"""You are an NBA betting analyst. You have been given ALL available data about an upcoming game.
Your job is to reason through this evidence step by step and produce a betting report.

GAME: {game_description}

=== HOME TEAM STATS ===
{evidence['home_team_stats']}

=== AWAY TEAM STATS ===
{evidence['away_team_stats']}

=== HEAD-TO-HEAD RECORD ===
{evidence['head_to_head']}

=== HOME TEAM INJURIES ===
{evidence['home_injuries']}

=== AWAY TEAM INJURIES ===
{evidence['away_injuries']}

=== HOME TEAM MEDIA / NEWS SENTIMENT ===
{evidence['home_team_sentiment']}

=== AWAY TEAM MEDIA / NEWS SENTIMENT ===
{evidence['away_team_sentiment']}

=== BETTING ODDS ===
{evidence['odds']}

=== SIMILAR HISTORICAL GAMES (HOME TEAM) ===
{evidence['similar_home']}

=== SIMILAR HISTORICAL GAMES (AWAY TEAM) ===
{evidence['similar_away']}

=== INFORMATION DENSITY ===
{json.dumps(evidence['_info_density'], indent=2)}

INSTRUCTIONS:
Think through this step by step. Consider each piece of evidence, weigh its importance,
and arrive at a prediction. Be explicit about your reasoning chain.

Use media/news sentiment and article coverage as a secondary contextual signal.
Do not let sentiment outweigh hard statistics, injuries, or market information.

If live odds are unavailable, explicitly explain that the selected matchup does not appear in the current upcoming-games odds feed. Say this usually means the selected teams are not actually scheduled to play each other in the current live odds dataset, and tell the user to choose a matchup that exists in the live odds feed to enable value assessment.

Then produce your analysis in this exact JSON format:

FINAL REPORT:
{{
    "game": "TEAM1 vs TEAM2",
    "date": "YYYY-MM-DD",
    "method": "chain_of_thought",
    "prediction": {{
        "home_win_prob": 0.XX,
        "away_win_prob": 0.XX,
        "confidence": "high/medium/low"
    }},
    "market_odds": {{
        "home_implied_prob": 0.XX,
        "away_implied_prob": 0.XX
    }},
    "key_factors": [
        {{"factor": "...", "impact": "favors_home/favors_away/neutral", "importance": "high/medium/low"}}
    ],
    "reasoning": "Your complete step-by-step reasoning chain...",
    "value_assessment": "Where do you see value vs the market? If no live odds are available, explicitly explain that the selected matchup does not appear in the current upcoming-games odds feed and tell the user to choose a matchup that exists in the live odds feed."
}}"""


# ============================================================
# LLM BACKENDS
# ============================================================

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


def call_openai(messages):
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=4096,
    )
    return response.choices[0].message.content


# ============================================================
# MAIN
# ============================================================

def run_cot_analysis(home_abbr, away_abbr, home_name, away_name, game_description, llm_call_fn):
    """
    Run the full CoT baseline:
    1. Gather all evidence (no agent decision-making)
    2. Send everything to the LLM in one prompt
    3. Get back a single-pass analysis
    """
    evidence = gather_all_evidence(home_abbr, away_abbr, home_name, away_name)
    prompt = build_cot_prompt(game_description, evidence)

    print("\nRunning chain-of-thought analysis (single pass)...")
    messages = [
        {"role": "user", "content": prompt},
    ]

    response = llm_call_fn(messages)

    return {
        "game": game_description,
        "method": "chain_of_thought",
        "evidence": evidence,
        "response": response,
        "llm_calls": 1,
        "info_density": evidence["_info_density"],
    }


def main():
    print("=" * 60)
    print("NBA CoT Baseline - Step 9")
    print("=" * 60)

    if os.environ.get("ANTHROPIC_API_KEY"):
        print("Using Claude (Anthropic) API")
        llm_fn = call_anthropic
    elif os.environ.get("OPENAI_API_KEY"):
        print("Using GPT-4 (OpenAI) API")
        llm_fn = call_openai
    else:
        print("No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        return

    result = run_cot_analysis(
        home_abbr="BOS",
        away_abbr="LAL",
        home_name="Boston Celtics",
        away_name="Los Angeles Lakers",
        game_description="Los Angeles Lakers vs Boston Celtics, March 30 2026",
        llm_call_fn=llm_fn,
    )

    print()
    print("=" * 60)
    print("COT BASELINE REPORT")
    print("=" * 60)

    response = result["response"]
    if "FINAL REPORT:" in response:
        report_text = response.split("FINAL REPORT:")[-1].strip()
        print(report_text)
    else:
        print(response)

    print()
    print(f"LLM calls: {result['llm_calls']}")
    print(f"Info density: {result['info_density']}")

    log_path = f"{DATA_DIR}/cot_baseline_log.json"
    save_data = {
        "game": result["game"],
        "method": result["method"],
        "response": result["response"],
        "llm_calls": result["llm_calls"],
        "info_density": result["info_density"],
        "timestamp": datetime.now().isoformat(),
    }
    with open(log_path, "w") as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"Log saved to {log_path}")

    print()
    print("=" * 60)
    print("TO COMPARE WITH MULTI-AGENT DEBATE:")
    print("=" * 60)
    print("Run: python3 nba_multi_agent.py")
    print("Then compare the predictions and reasoning quality")
    print("between cot_baseline_log.json and multi_agent_log.json")


if __name__ == "__main__":
    main()