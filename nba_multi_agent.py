"""
Step 8: Multi-Agent Debate System
Three agents with different analytical perspectives and tool access
debate an NBA game across iterative rounds.

Agents:
  1. Stats Agent - focuses on numbers (scoring, defense, pace, efficiency)
     Tools: get_team_stats, get_head_to_head, search_similar_games (quantitative only)
  
  2. Matchup Agent - focuses on context (schedule, travel, rest, coaching, sentiment)
     Tools: get_injuries, search_similar_games (contextual), news/reddit (when available)
  
  3. Market Agent - starts from the odds and confirms or challenges them
     Tools: get_odds, get_team_stats, get_injuries, search_similar_games (any)

Debate flow:
  Round 1: Each agent independently analyzes and predicts
  Round 2: Each agent sees the others' arguments and responds
  Round 3 (optional): Final positions after seeing rebuttals
  Moderator: Synthesizes into a final report

Usage:
    export ANTHROPIC_API_KEY="your_key"   (or OPENAI_API_KEY)
    python nba_multi_agent.py

Requires: steps 1-3, 6, and 7 to be completed
"""

import os
import json
from datetime import datetime

# Import tools from the single agent
from nba_agent import (
    tool_get_team_stats,
    tool_get_head_to_head,
    tool_get_injuries,
    tool_get_odds,
    tool_search_similar_games,
    parse_action,
    DATA_DIR,
)


# ============================================================
# AGENT DEFINITIONS
# ============================================================

AGENTS = {
    "stats_agent": {
        "name": "Stats & Metrics Agent",
        "tools": {
            "get_team_stats": tool_get_team_stats,
            "get_head_to_head": tool_get_head_to_head,
            "search_similar_games": tool_search_similar_games,
        },
        "system_prompt": """You are the Stats & Metrics Agent. You analyze NBA games purely through numbers.

You focus on: scoring averages, defensive rating, pace, field goal percentages, 
rebounding, assists, turnovers, plus/minus, and historical statistical patterns.

You have access to these tools ONLY:
  - get_team_stats(team_abbr, season): Get team's recent stats and record
  - get_head_to_head(team1_abbr, team2_abbr): Get H2H record between teams
  - search_similar_games(query_text, team, n_results): Search historical games by stats

RULES:
- You MUST call at least 2 tools before giving your analysis.
- Call ONE tool per response.
- Base every claim on data from tool observations. Do not make up numbers.
- When calling a tool, use: ACTION: tool_name(arg1="value1")

After gathering data, provide your analysis in this format:

ANALYSIS:
{
    "agent": "stats_agent",
    "prediction": {"home_win_prob": 0.XX, "away_win_prob": 0.XX},
    "confidence": "high/medium/low",
    "key_points": ["point 1", "point 2", "point 3"],
    "reasoning": "Your statistical reasoning..."
}

Start by calling get_team_stats for the home team.""",
    },

    "matchup_agent": {
        "name": "Matchup & Context Agent",
        "tools": {
            "get_injuries": tool_get_injuries,
            "search_similar_games": tool_search_similar_games,
        },
        "system_prompt": """You are the Matchup & Context Agent. You analyze NBA games through situational context.

You focus on: injuries and their impact, schedule factors (back-to-backs, rest days, 
travel), home/away dynamics, coaching matchups, momentum, and team narrative.

You have access to these tools ONLY:
  - get_injuries(team_name): Get current injury report for a team
  - search_similar_games(query_text, team, n_results): Search for historically similar situations

RULES:
- You MUST call at least 2 tools before giving your analysis.
- Call ONE tool per response.
- Base every claim on data from tool observations. Do not make up numbers.
- When calling a tool, use: ACTION: tool_name(arg1="value1")

After gathering data, provide your analysis in this format:

ANALYSIS:
{
    "agent": "matchup_agent",
    "prediction": {"home_win_prob": 0.XX, "away_win_prob": 0.XX},
    "confidence": "high/medium/low",
    "key_points": ["point 1", "point 2", "point 3"],
    "reasoning": "Your contextual reasoning..."
}

Start by calling get_injuries for the home team.""",
    },

    "market_agent": {
        "name": "Market & Odds Agent",
        "tools": {
            "get_odds": tool_get_odds,
            "get_team_stats": tool_get_team_stats,
            "get_injuries": tool_get_injuries,
            "search_similar_games": tool_search_similar_games,
        },
        "system_prompt": """You are the Market & Odds Agent. You start from the bookmaker odds and try to 
confirm or challenge them.

You focus on: what the market thinks, where the line has moved, whether the odds 
reflect the true probabilities, and where there might be value.

You have access to these tools:
  - get_odds(home_team, away_team): Get current odds from multiple sportsbooks
  - get_team_stats(team_abbr, season): Get team stats to cross-check market pricing
  - get_injuries(team_name): Check if injuries are properly priced in
  - search_similar_games(query_text, team, n_results): Find historical precedent

RULES:
- You MUST call get_odds first, then at least 1 more tool.
- Call ONE tool per response.
- Base every claim on data from tool observations. Do not make up numbers.
- When calling a tool, use: ACTION: tool_name(arg1="value1")

After gathering data, provide your analysis in this format:

ANALYSIS:
{
    "agent": "market_agent",
    "prediction": {"home_win_prob": 0.XX, "away_win_prob": 0.XX},
    "market_implied": {"home_win_prob": 0.XX, "away_win_prob": 0.XX},
    "value_spots": ["any value bets identified"],
    "confidence": "high/medium/low",
    "key_points": ["point 1", "point 2", "point 3"],
    "reasoning": "Your market-based reasoning..."
}

Start by calling get_odds for this game.""",
    },
}


# ============================================================
# AGENT RUNNER
# ============================================================

def run_single_agent(agent_key, game_description, llm_call_fn, extra_context="", max_steps=5):
    """
    Run a single agent's data gathering and analysis phase.
    Returns the agent's analysis.
    """
    agent = AGENTS[agent_key]
    print(f"\n{'='*50}")
    print(f"  {agent['name']}")
    print(f"{'='*50}")

    system_prompt = agent["system_prompt"]
    if extra_context:
        system_prompt += f"\n\nCONTEXT FROM OTHER AGENTS:\n{extra_context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this game: {game_description}"},
    ]

    step = 0
    while step < max_steps:
        response_text = llm_call_fn(messages)

        # Check if agent produced analysis
        if "ANALYSIS:" in response_text:
            print(f"  Step {step+1}: ANALYSIS produced")
            return response_text

        # Parse and execute action
        tool_name, kwargs, action_line = parse_action(response_text)

        if tool_name:
            # Check if agent has access to this tool
            if tool_name in agent["tools"]:
                print(f"  Step {step+1}: {tool_name}({kwargs})")
                result = agent["tools"][tool_name](**kwargs)
                if len(str(result)) > 3000:
                    result = str(result)[:3000] + "\n... (truncated)"
                print(f"    -> {str(result)[:120]}...")

                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": f"OBSERVATION: {result}"})
            else:
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": 
                    f"ERROR: You don't have access to {tool_name}. Your tools are: {list(agent['tools'].keys())}"})
                print(f"  Step {step+1}: DENIED {tool_name} (not in this agent's tools)")
        else:
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": "Continue. Call a tool or produce your ANALYSIS."})

        step += 1

    # Force analysis if max steps reached
    messages.append({"role": "user", "content": "Produce your ANALYSIS now based on the data you have."})
    response_text = llm_call_fn(messages)
    return response_text


def extract_analysis(response_text):
    """Extract the JSON analysis from an agent's response."""
    if "ANALYSIS:" not in response_text:
        return None
    try:
        json_str = response_text.split("ANALYSIS:")[-1].strip()
        # Find the JSON object
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(json_str[start:end])
    except json.JSONDecodeError:
        pass
    return None


def run_debate_round(game_description, agent_analyses, round_num, llm_call_fn):
    """
    Run a debate round where each agent sees and responds to the others' analyses.
    """
    print(f"\n{'#'*60}")
    print(f"  DEBATE ROUND {round_num}")
    print(f"{'#'*60}")

    updated_analyses = {}

    for agent_key in AGENTS:
        # Build context from other agents
        other_analyses = []
        for other_key, analysis in agent_analyses.items():
            if other_key != agent_key:
                other_name = AGENTS[other_key]["name"]
                other_analyses.append(f"{other_name}:\n{json.dumps(analysis, indent=2)}")

        context = "\n\n".join(other_analyses)
        debate_prompt = f"""The other agents have shared their analyses. Review their arguments 
and update your position if warranted. You may agree, disagree, or adjust your prediction.

If you want to gather more data to challenge their claims, you can call a tool first.
Otherwise, provide your updated ANALYSIS directly.

Other agents' positions:
{context}"""

        agent = AGENTS[agent_key]
        messages = [
            {"role": "system", "content": agent["system_prompt"]},
            {"role": "user", "content": f"Game: {game_description}\n\n{debate_prompt}"},
        ]

        print(f"\n  {agent['name']} responding to debate...")

        # Allow one tool call then analysis
        response_text = llm_call_fn(messages)

        # If agent wants to call a tool
        tool_name, kwargs, _ = parse_action(response_text)
        if tool_name and tool_name in agent["tools"]:
            print(f"    Tool call: {tool_name}({kwargs})")
            result = agent["tools"][tool_name](**kwargs)
            if len(str(result)) > 2000:
                result = str(result)[:2000] + "\n... (truncated)"

            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"OBSERVATION: {result}\n\nNow provide your updated ANALYSIS."})
            response_text = llm_call_fn(messages)

        analysis = extract_analysis(response_text)
        if analysis:
            updated_analyses[agent_key] = analysis
            pred = analysis.get("prediction", {})
            print(f"    Updated prediction: Home {pred.get('home_win_prob', '?')} | Away {pred.get('away_win_prob', '?')}")
        else:
            # Keep old analysis if parsing failed
            updated_analyses[agent_key] = agent_analyses.get(agent_key, {})
            print(f"    Kept previous position (parse failed)")

    return updated_analyses


def moderate(game_description, agent_analyses, llm_call_fn):
    """
    Moderator synthesizes all agents' analyses into a final report.
    """
    print(f"\n{'#'*60}")
    print(f"  MODERATOR SYNTHESIS")
    print(f"{'#'*60}")

    analyses_text = ""
    for agent_key, analysis in agent_analyses.items():
        agent_name = AGENTS[agent_key]["name"]
        analyses_text += f"\n{agent_name}:\n{json.dumps(analysis, indent=2)}\n"

    moderator_prompt = f"""You are the Moderator. Three specialized agents have analyzed this NBA game 
and debated their positions. Your job is to synthesize their analyses into one final betting report.

Game: {game_description}

Agent Analyses:
{analyses_text}

Consider:
- Where do the agents agree? Those are high-confidence findings.
- Where do they disagree? Weigh each agent's reasoning and data quality.
- The Stats Agent is most reliable for performance metrics.
- The Matchup Agent is most reliable for injury impact and schedule effects.
- The Market Agent is most reliable for understanding what the odds already reflect.

Produce the FINAL REPORT in this JSON format:
{{
    "game": "TEAM1 vs TEAM2",
    "date": "YYYY-MM-DD",
    "method": "multi-agent debate",
    "agent_predictions": {{
        "stats_agent": {{"home": X.XX, "away": X.XX}},
        "matchup_agent": {{"home": X.XX, "away": X.XX}},
        "market_agent": {{"home": X.XX, "away": X.XX}}
    }},
    "synthesized_prediction": {{
        "home_win_prob": 0.XX,
        "away_win_prob": 0.XX,
        "confidence": "high/medium/low"
    }},
    "market_odds": {{
        "home_implied_prob": 0.XX,
        "away_implied_prob": 0.XX
    }},
    "key_factors": [
        {{"factor": "...", "impact": "favors_home/favors_away/neutral", "importance": "high/medium/low", "source_agent": "..."}}
    ],
    "areas_of_agreement": ["..."],
    "areas_of_disagreement": ["..."],
    "reasoning": "Step-by-step synthesis...",
    "value_assessment": "Where does the synthesized view differ from the market?"
}}"""

    messages = [
        {"role": "system", "content": "You are a moderator synthesizing multiple expert analyses into a final betting report. Use only the data provided by the agents. Do not introduce new information."},
        {"role": "user", "content": moderator_prompt},
    ]

    response = llm_call_fn(messages)
    return response


# ============================================================
# LLM BACKENDS (same as nba_agent.py)
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
        system=system_msg,
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

def run_full_debate(game_description, llm_call_fn, num_debate_rounds=2):
    """
    Run the full multi-agent debate pipeline.
    
    1. Each agent independently gathers data and analyzes
    2. Agents debate for num_debate_rounds rounds
    3. Moderator synthesizes final report
    """
    print("=" * 60)
    print(f"MULTI-AGENT DEBATE: {game_description}")
    print("=" * 60)

    # Phase 1: Independent analysis
    print(f"\n{'#'*60}")
    print(f"  PHASE 1: INDEPENDENT ANALYSIS")
    print(f"{'#'*60}")

    agent_analyses = {}
    agent_raw_responses = {}

    for agent_key in AGENTS:
        response = run_single_agent(agent_key, game_description, llm_call_fn)
        agent_raw_responses[agent_key] = response
        analysis = extract_analysis(response)
        if analysis:
            agent_analyses[agent_key] = analysis
            pred = analysis.get("prediction", {})
            print(f"  -> Prediction: Home {pred.get('home_win_prob', '?')} | Away {pred.get('away_win_prob', '?')}")
        else:
            agent_analyses[agent_key] = {"error": "Failed to parse analysis", "raw": response[:500]}
            print(f"  -> Failed to parse analysis")

    # Phase 2: Debate rounds
    for round_num in range(1, num_debate_rounds + 1):
        agent_analyses = run_debate_round(game_description, agent_analyses, round_num, llm_call_fn)

    # Phase 3: Moderator synthesis
    final_report = moderate(game_description, agent_analyses, llm_call_fn)

    return {
        "game": game_description,
        "agent_analyses": agent_analyses,
        "final_report": final_report,
        "num_debate_rounds": num_debate_rounds,
    }


def main():
    print("=" * 60)
    print("NBA Multi-Agent Debate - Step 8")
    print("=" * 60)

    # Choose LLM backend
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("Using Claude (Anthropic) API")
        llm_fn = call_anthropic
    elif os.environ.get("OPENAI_API_KEY"):
        print("Using GPT-4 (OpenAI) API")
        llm_fn = call_openai
    else:
        print("No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        return

    # Test game
    game = "Los Angeles Lakers vs Boston Celtics, March 30 2026"

    result = run_full_debate(game, llm_fn, num_debate_rounds=2)

    # Print final report
    print()
    print("=" * 60)
    print("FINAL SYNTHESIZED REPORT")
    print("=" * 60)
    print(result["final_report"])

    # Save everything
    log_path = f"{DATA_DIR}/multi_agent_log.json"
    save_data = {
        "game": result["game"],
        "agent_analyses": result["agent_analyses"],
        "final_report": result["final_report"],
        "num_debate_rounds": result["num_debate_rounds"],
        "timestamp": datetime.now().isoformat(),
    }
    with open(log_path, "w") as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"\nFull debate log saved to {log_path}")

    # Print comparison
    print()
    print("=" * 60)
    print("AGENT PREDICTION COMPARISON")
    print("=" * 60)
    for agent_key, analysis in result["agent_analyses"].items():
        name = AGENTS[agent_key]["name"]
        pred = analysis.get("prediction", {})
        conf = analysis.get("confidence", "?")
        print(f"  {name}: Home {pred.get('home_win_prob', '?')} | Away {pred.get('away_win_prob', '?')} (confidence: {conf})")


if __name__ == "__main__":
    main()
