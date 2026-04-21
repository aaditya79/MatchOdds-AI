"""
Step 7: NBA Betting Agent
ReAct-style agent that gathers data from multiple tools and produces
a structured pre-game betting report.

This is the core of the project. The agent:
1. Takes an upcoming game (e.g., "LAL vs BOS")
2. Plans which tools to call
3. Gathers data iteratively (odds, stats, injuries, vector store)
4. Reasons through the evidence
5. Produces a structured betting report with win probabilities

Usage:
    export ANTHROPIC_API_KEY="your_key_here"  (or OPENAI_API_KEY)
    python nba_agent.py

Requires: steps 1-3 and 6 to be completed (data/ and chroma_db/ populated)
"""

import os
import json
import pandas as pd
from datetime import datetime

# ============================================================
# TOOL DEFINITIONS - each tool queries a different data source
# ============================================================

DATA_DIR = "data"


def tool_get_team_stats(team_abbr, season="2024-25"):
    """Get recent team stats and form."""
    try:
        game_logs = pd.read_csv(f"{DATA_DIR}/game_logs.csv")
        team_games = game_logs[
            (game_logs["TEAM_ABBREVIATION"] == team_abbr) &
            (game_logs["SEASON"] == season)
        ].sort_values("GAME_DATE", ascending=False)

        if team_games.empty:
            return f"No data found for {team_abbr} in {season}."

        last_10 = team_games.head(10)
        season_record = team_games

        result = {
            "team": team_abbr,
            "season": season,
            "season_record": f"{int(season_record['WIN'].sum())}-{int((season_record['WIN'] == 0).sum())}",
            "last_10_record": f"{int(last_10['WIN'].sum())}-{int((last_10['WIN'] == 0).sum())}",
            "avg_points_last_10": round(last_10["PTS"].mean(), 1),
            "avg_fg_pct_last_10": round(last_10["FG_PCT"].mean(), 3),
            "avg_fg3_pct_last_10": round(last_10["FG3_PCT"].mean(), 3),
            "avg_rebounds_last_10": round(last_10["REB"].mean(), 1),
            "avg_assists_last_10": round(last_10["AST"].mean(), 1),
            "avg_turnovers_last_10": round(last_10["TOV"].mean(), 1),
            "avg_plus_minus_last_10": round(last_10["PLUS_MINUS"].mean(), 1),
            "last_game": {
                "date": str(team_games.iloc[0]["GAME_DATE"])[:10],
                "matchup": team_games.iloc[0]["MATCHUP"],
                "result": "W" if team_games.iloc[0]["WIN"] == 1 else "L",
                "points": int(team_games.iloc[0]["PTS"]),
            },
            "back_to_back_today": int(team_games.iloc[0].get("BACK_TO_BACK", 0)) if len(team_games) > 0 else 0,
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting stats for {team_abbr}: {e}"


def tool_get_head_to_head(team1_abbr, team2_abbr):
    """Get head-to-head record between two teams."""
    try:
        h2h = pd.read_csv(f"{DATA_DIR}/head_to_head.csv")
        matchup = h2h[
            (h2h["TEAM_ABBREVIATION"] == team1_abbr) &
            (h2h["OPPONENT_ABB"] == team2_abbr)
        ]

        if matchup.empty:
            return f"No H2H data for {team1_abbr} vs {team2_abbr}."

        result = {
            "matchup": f"{team1_abbr} vs {team2_abbr}",
            "seasons": [],
        }
        for _, row in matchup.iterrows():
            result["seasons"].append({
                "season": row["SEASON"],
                "games": int(row["GAMES"]),
                "wins": int(row["WINS"]),
                "losses": int(row["LOSSES"]),
                "win_pct": round(row["WIN_PCT"], 3),
                "avg_points": round(row["AVG_PTS"], 1),
                "avg_plus_minus": round(row["AVG_PLUS_MINUS"], 1),
            })

        total_games = matchup["GAMES"].sum()
        total_wins = matchup["WINS"].sum()
        result["overall"] = {
            "total_games": int(total_games),
            "total_wins": int(total_wins),
            "total_losses": int(total_games - total_wins),
            "overall_win_pct": round(total_wins / total_games, 3) if total_games > 0 else 0,
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting H2H: {e}"


def tool_get_injuries(team_name=None):
    """Get current injury report. Optionally filter by team."""
    try:
        injuries = pd.read_csv(f"{DATA_DIR}/injuries.csv")
        if injuries.empty:
            return "No injury data available."

        if team_name:
            # Fuzzy match on team name
            team_injuries = injuries[
                injuries["TEAM"].str.contains(team_name, case=False, na=False)
            ]
        else:
            team_injuries = injuries

        if team_injuries.empty:
            return f"No injuries found for {team_name}."

        result = []
        for _, row in team_injuries.iterrows():
            result.append({
                "team": row.get("TEAM", ""),
                "player": row.get("PLAYER_NAME", ""),
                "position": row.get("POSITION", ""),
                "status": row.get("STATUS", ""),
                "est_return": row.get("EST_RETURN", ""),
                "comment": str(row.get("COMMENT", ""))[:200],
            })
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting injuries: {e}"


def tool_get_odds(home_team=None, away_team=None):
    """Get current betting odds for upcoming games."""
    try:
        odds = pd.read_csv(f"{DATA_DIR}/odds_live.csv")
        if odds.empty:
            return "No live odds data available."

        # Filter to moneyline (h2h) market
        h2h_odds = odds[odds["MARKET"] == "h2h"]

        if home_team:
            h2h_odds = h2h_odds[
                (h2h_odds["HOME_TEAM"].str.contains(home_team, case=False, na=False)) |
                (h2h_odds["AWAY_TEAM"].str.contains(home_team, case=False, na=False))
            ]
        if away_team:
            h2h_odds = h2h_odds[
                (h2h_odds["HOME_TEAM"].str.contains(away_team, case=False, na=False)) |
                (h2h_odds["AWAY_TEAM"].str.contains(away_team, case=False, na=False))
            ]

        if h2h_odds.empty:
            return f"No odds found for {home_team} vs {away_team}."

        # Group by game and summarize
        games = {}
        for _, row in h2h_odds.iterrows():
            game_id = row["GAME_ID"]
            if game_id not in games:
                games[game_id] = {
                    "home_team": row["HOME_TEAM"],
                    "away_team": row["AWAY_TEAM"],
                    "commence_time": row["COMMENCE_TIME"],
                    "bookmakers": {},
                }
            book = row["BOOKMAKER"]
            if book not in games[game_id]["bookmakers"]:
                games[game_id]["bookmakers"][book] = {}
            games[game_id]["bookmakers"][book][row["OUTCOME_NAME"]] = {
                "price": row["PRICE"],
                "implied_prob": round(row.get("IMPLIED_PROB", 0), 3),
            }

        return json.dumps(list(games.values()), indent=2)
    except Exception as e:
        return f"Error getting odds: {e}"


def tool_search_similar_games(query_text, team=None, n_results=5):
    """Search the vector store for historically similar games."""
    try:
        from nba_vector_store import query_similar_games

        where_filter = None
        if team:
            where_filter = {"team": team}

        results = query_similar_games(query_text, n_results=n_results, where_filter=where_filter)

        output = []
        for i in range(len(results["documents"][0])):
            output.append({
                "game_description": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
            })
        return json.dumps(output, indent=2)
    except Exception as e:
        return f"Error searching similar games: {e}"


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOLS = {
    "get_team_stats": {
        "function": tool_get_team_stats,
        "description": "Get a team's recent stats, record, and form. Args: team_abbr (e.g. 'LAL', 'BOS'), season (optional, default '2024-25')",
    },
    "get_head_to_head": {
        "function": tool_get_head_to_head,
        "description": "Get head-to-head record between two teams. Args: team1_abbr, team2_abbr",
    },
    "get_injuries": {
        "function": tool_get_injuries,
        "description": "Get current injury report for a team. Args: team_name (e.g. 'Lakers', 'Celtics')",
    },
    "get_odds": {
        "function": tool_get_odds,
        "description": "Get current betting odds from multiple sportsbooks. Args: home_team, away_team (team city names)",
    },
    "search_similar_games": {
        "function": tool_search_similar_games,
        "description": "Search historical games for similar situations. Args: query_text (natural language), team (optional, team abbreviation), n_results (optional, default 5)",
    },
}


# ============================================================
# AGENT LOGIC
# ============================================================

def build_system_prompt():
    """Build the system prompt for the ReAct agent."""
    tool_descriptions = "\n".join([
        f"  - {name}: {info['description']}"
        for name, info in TOOLS.items()
    ])

    return f"""You are an NBA pre-game betting analyst. Your job is to analyze an upcoming NBA game 
and produce a structured betting report.

CRITICAL RULES:
- You MUST call tools to get real data. Do NOT use your own knowledge for any stats, odds, records, or injury info.
- You MUST call at least 4 different tools before producing a FINAL REPORT.
- Every number in your report must come from a tool observation, not from your training data.
- If you produce a FINAL REPORT without calling tools first, it will be rejected.
- Call ONE tool per response. Do not call multiple tools in the same message.

You have access to the following tools:
{tool_descriptions}

Follow the ReAct pattern:
1. THOUGHT: Think about what information you need next
2. ACTION: Call exactly one tool to get that information
3. Wait for the OBSERVATION (the tool result will be provided to you)
4. Repeat steps 1-3 until you have called at least 4 tools and gathered enough data
5. FINAL REPORT: Only after gathering real data, produce the structured betting report

When calling a tool, use this exact format (one tool per message):
ACTION: tool_name(arg1="value1", arg2="value2")

START by calling get_team_stats for the home team. Do NOT skip to the final report.

When you have gathered enough information from tools, produce a FINAL REPORT with this structure:

FINAL REPORT:
{{
    "game": "TEAM1 vs TEAM2",
    "date": "YYYY-MM-DD",
    "market_odds": {{
        "home_team": {{"name": "...", "avg_implied_prob": 0.XX}},
        "away_team": {{"name": "...", "avg_implied_prob": 0.XX}}
    }},
    "agent_prediction": {{
        "home_win_prob": 0.XX,
        "away_win_prob": 0.XX,
        "confidence": "high/medium/low"
    }},
    "key_factors": [
        {{"factor": "...", "impact": "favors_home/favors_away/neutral", "importance": "high/medium/low"}},
    ],
    "reasoning": "Step-by-step reasoning chain...",
    "value_assessment": "Does the agent see value vs the market? Where and why?"
}}

Be thorough but efficient. Gather stats for both teams, check injuries, look at odds, 
and search for historical precedent. Then reason through it all step by step."""


def parse_action(text):
    """Parse an ACTION line from the agent's response."""
    if "ACTION:" not in text:
        return None, None, None

    action_line = text.split("ACTION:")[-1].strip().split("\n")[0]

    # Parse tool_name(arg1="val1", arg2="val2")
    if "(" not in action_line:
        return None, None, None

    tool_name = action_line.split("(")[0].strip()
    args_str = action_line.split("(", 1)[1].rsplit(")", 1)[0]

    # Parse keyword arguments
    kwargs = {}
    if args_str.strip():
        # Handle both key="value" and key=value formats
        import re
        pairs = re.findall(r'(\w+)\s*=\s*"([^"]*)"', args_str)
        if not pairs:
            pairs = re.findall(r'(\w+)\s*=\s*([^,\)]+)', args_str)

        for key, val in pairs:
            kwargs[key.strip()] = val.strip().strip('"').strip("'")

    return tool_name, kwargs, action_line


def call_tool(tool_name, kwargs):
    """Execute a tool call and return the result."""
    if tool_name not in TOOLS:
        return f"Unknown tool: {tool_name}. Available tools: {list(TOOLS.keys())}"

    func = TOOLS[tool_name]["function"]
    try:
        result = func(**kwargs)
        return result
    except TypeError as e:
        return f"Error calling {tool_name}: {e}. Check your arguments."
    except Exception as e:
        return f"Error: {e}"


def run_agent(game_description, llm_call_fn, max_steps=8):
    """
    Run the ReAct agent loop.

    Args:
        game_description: e.g. "Los Angeles Lakers vs Boston Celtics, March 30 2026"
        llm_call_fn: function that takes messages list and returns response text
        max_steps: maximum number of tool calls before forcing final report

    Returns:
        dict with the conversation history and final report
    """
    system_prompt = build_system_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this upcoming game and produce a betting report: {game_description}"},
    ]

    conversation_log = []
    step = 0

    print(f"\nAnalyzing: {game_description}")
    print("=" * 60)

    while step < max_steps:
        # Call the LLM
        response_text = llm_call_fn(messages)

        # Log it
        conversation_log.append({
            "step": step + 1,
            "role": "assistant",
            "content": response_text,
        })

        # Check if we have a final report
        if "FINAL REPORT:" in response_text:
            print(f"\nStep {step + 1}: FINAL REPORT generated")
            return {
                "conversation": conversation_log,
                "final_response": response_text,
                "steps": step + 1,
            }

        # Parse and execute action
        tool_name, kwargs, action_line = parse_action(response_text)

        if tool_name:
            print(f"Step {step + 1}: ACTION - {tool_name}({kwargs})")

            # Call the tool
            observation = call_tool(tool_name, kwargs)

            # Truncate long observations
            if len(observation) > 3000:
                observation = observation[:3000] + "\n... (truncated)"

            print(f"  OBSERVATION: {observation[:150]}...")

            # Add to conversation
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"OBSERVATION: {observation}"})

            conversation_log.append({
                "step": step + 1,
                "role": "tool",
                "tool": tool_name,
                "args": kwargs,
                "result": observation[:500],
            })
        else:
            # No action found, add response and ask agent to continue
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": "Continue your analysis. Use a tool or produce the FINAL REPORT."})

        step += 1

    # If we hit max steps, ask for final report
    messages.append({"role": "user", "content": "You've gathered enough data. Produce the FINAL REPORT now."})
    response_text = llm_call_fn(messages)
    conversation_log.append({
        "step": step + 1,
        "role": "assistant",
        "content": response_text,
    })

    return {
        "conversation": conversation_log,
        "final_response": response_text,
        "steps": step + 1,
    }


# ============================================================
# LLM CALL FUNCTIONS (choose one)
# ============================================================

def call_anthropic(messages):
    """Call Claude API."""
    import anthropic

    client = anthropic.Anthropic()

    # Convert messages format: separate system from conversation
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
        system=system_msg,
        messages=conv_messages,
    )
    return response.content[0].text


def call_openai(messages):
    """Call OpenAI API."""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def call_mock(messages):
    """Mock LLM for testing without API keys."""
    last_msg = messages[-1]["content"]

    if "Analyze this upcoming game" in last_msg:
        return """THOUGHT: I need to gather information about both teams. Let me start with the home team's stats.

ACTION: get_team_stats(team_abbr="LAL")"""

    elif "OBSERVATION" in last_msg and "get_team_stats" in str(messages[-3].get("content", "")):
        if "LAL" in str(messages[-3].get("content", "")):
            return """THOUGHT: Got Lakers stats. Now let me get the away team's stats.

ACTION: get_team_stats(team_abbr="BOS")"""
        else:
            return """THOUGHT: Got both teams' stats. Let me check the odds.

ACTION: get_odds(home_team="Lakers", away_team="Celtics")"""

    elif "OBSERVATION" in last_msg and "get_odds" in str(messages[-3].get("content", "")):
        return """THOUGHT: Got the odds. Let me check injuries for both teams.

ACTION: get_injuries(team_name="Lakers")"""

    elif "OBSERVATION" in last_msg and "injuries" in str(messages[-3].get("content", "")).lower():
        return """THOUGHT: I have enough information. Let me produce the final report.

FINAL REPORT:
{
    "game": "LAL vs BOS",
    "date": "2026-03-30",
    "market_odds": {
        "home_team": {"name": "Los Angeles Lakers", "avg_implied_prob": 0.45},
        "away_team": {"name": "Boston Celtics", "avg_implied_prob": 0.55}
    },
    "agent_prediction": {
        "home_win_prob": 0.42,
        "away_win_prob": 0.58,
        "confidence": "medium"
    },
    "key_factors": [
        {"factor": "Mock analysis - replace with real LLM", "impact": "neutral", "importance": "high"}
    ],
    "reasoning": "This is a mock response for testing. Use a real LLM API for actual analysis.",
    "value_assessment": "Mock assessment. No real value detected in this test."
}"""

    else:
        return """THOUGHT: Let me continue gathering data.

ACTION: get_team_stats(team_abbr="BOS")"""


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("NBA Betting Agent - Step 7")
    print("=" * 60)

    # Choose LLM backend
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("Using Claude (Anthropic) API")
        llm_fn = call_anthropic
    elif os.environ.get("OPENAI_API_KEY"):
        print("Using GPT-4 (OpenAI) API")
        llm_fn = call_openai
    else:
        print("No API key found. Using mock LLM for testing.")
        print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY for real analysis.")
        llm_fn = call_mock

    # Test game
    game = "Los Angeles Lakers vs Boston Celtics, March 30 2026"

    result = run_agent(game, llm_fn)

    # Print final report
    print()
    print("=" * 60)
    print("FINAL REPORT")
    print("=" * 60)

    # Extract the report JSON from the response
    final = result["final_response"]
    if "FINAL REPORT:" in final:
        report_text = final.split("FINAL REPORT:")[-1].strip()
        print(report_text)
    else:
        print(final)

    print()
    print(f"Total agent steps: {result['steps']}")
    print()

    # Save the full conversation log
    log_path = f"{DATA_DIR}/agent_log.json"
    with open(log_path, "w") as f:
        json.dump(result["conversation"], f, indent=2)
    print(f"Conversation log saved to {log_path}")


if __name__ == "__main__":
    main()