# agents.py
# Enhanced with detailed orchestration logs for Foresters Financial Challenge
# Shows state transformations and agent hand-offs clearly

import json
import re
from typing import Dict, Any

from google import genai
from google.genai import types
from dotenv import load_dotenv
from config import get_settings
from schemas import MindMoneyState

load_dotenv()

# --- SHARED UTILS ---
def get_gemini_client():
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)


def safe_parse_json(response_text: str | None) -> Dict[str, Any]:
    if not response_text:
        return {}
    try:
        text = re.sub(r'```json\s*', '', response_text)
        text = re.sub(r'```\s*', '', text)
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}


def truncate_for_log(data: Any, max_length: int = 200) -> str:
    """Truncate data for readable logs."""
    text = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


# ============================================================================
# AGENT 1: INTAKE SPECIALIST (The Router & Empath)
# ============================================================================
INTAKE_PROMPT = """You are an Intake Specialist in financial wellness. 

Your Goals:
1. Assess the user's emotional state (ALWAYS do this).
2. Determine if the user has provided enough specific financial data to generate a plan.

CATEGORIZATION RULES:
- "GREETING": User says hello, asks "what is this?", general small talk, or asks what you can do.
- "CLARIFICATION": User mentions a financial problem ("I'm broke", "I have debt", "I want to buy a house") but gives NO specific numbers or amounts.
- "DATA_SUBMISSION": User provides specific financial data like income amounts, debt amounts, savings, or concrete goals with numbers (e.g., "$50k debt", "I make $4000/month", "I owe 5000 on my credit card").

Be careful: Vague statements like "I have debt" or "I'm struggling" are CLARIFICATION, not DATA_SUBMISSION.
Only classify as DATA_SUBMISSION if the user provides actual numbers.

OUTPUT ONLY VALID JSON:
{
  "intent": "GREETING" | "CLARIFICATION" | "DATA_SUBMISSION",
  "emotional_state": {
    "anxiety": 0-10,
    "shame": 0-10,
    "overwhelm": 0-10,
    "hope": 0-10,
    "primary_emotion": "string describing their main feeling"
  },
  "financial_psychology": {
    "money_beliefs": ["any beliefs about money you detect"],
    "triggers": ["emotional triggers around money"]
  },
  "rapport_indicators": {
    "engagement_level": "low|medium|high",
    "trust_needed": ["validation", "competence", "confidentiality"]
  },
  "safety_concerns": {
    "crisis_flag": false,
    "escalation_needed": false
  },
  "validation_hook": "A compassionate, specific sentence validating their situation or emotion.",
  "missing_info": ["List 1-3 specific things needed to build a plan - ONLY if intent is CLARIFICATION. Examples: 'monthly income', 'total debt amount', 'monthly expenses'"]
}"""


async def run_intake_agent(state: MindMoneyState):
    """
    AGENT 1: Intake Specialist
    - Analyzes user input for intent and emotional state
    - Routes to appropriate downstream agents
    - First agent in the pipeline - receives raw user input
    """
    settings = get_settings()
    client = get_gemini_client()
    
    # =========== INPUT STATE ===========
    input_state = {
        "user_input": state['user_input'][:100] + "..." if len(state['user_input']) > 100 else state['user_input'],
        "history_length": len(state.get("conversation_history", [])),
        "existing_intake_profile": bool(state.get("intake_profile")),
        "existing_financial_profile": bool(state.get("financial_profile"))
    }
    
    # Build conversation context
    history_context = ""
    if state.get("conversation_history"):
        history_context = "\n".join([
            f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
            for msg in state["conversation_history"][-4:]
        ])
    
    try:
        messages = f"{history_context}\nCURRENT MESSAGE:\n{state['user_input']}" if history_context else state['user_input']
        
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {INTAKE_PROMPT}\nCONTEXT:\n{messages}",
            config=types.GenerateContentConfig(
                temperature=settings.intake_temperature,
                response_mime_type="application/json"
            )
        )
        data = safe_parse_json(response.text)
        
        # Extract key fields
        intent = data.get("intent", "GREETING")
        emotions = data.get("emotional_state", {})
        primary_emotion = emotions.get("primary_emotion", "neutral")
        anxiety = emotions.get("anxiety", 0)
        shame = emotions.get("shame", 0)
        safety = data.get("safety_concerns", {})
        missing_info = data.get("missing_info", [])
        
        # =========== OUTPUT STATE ===========
        output_state = {
            "intent": intent,
            "anxiety_score": anxiety,
            "shame_score": shame,
            "primary_emotion": primary_emotion,
            "crisis_flag": safety.get("crisis_flag", False),
            "missing_info": missing_info[:2] if missing_info else [],
            "routing_decision": "→ Wealth Architect + Market Researcher" if intent == "DATA_SUBMISSION" else "→ Care Manager (skip analysis)"
        }
        
        # =========== ENHANCED LOG ===========
        log = {
            "agent": "Intake Specialist",
            "role": "Emotional Assessment & Intent Classification",
            "thought": f"Classified as {intent}. User feels {primary_emotion} (anxiety: {anxiety}/10, shame: {shame}/10). {f'Missing: {missing_info[:2]}' if missing_info else 'Has sufficient data.' if intent == 'DATA_SUBMISSION' else ''}",
            "status": "complete",
            "input_state": input_state,
            "output_state": output_state,
            "state_changes": {
                "added": ["intake_profile.intent", "intake_profile.emotional_state", "intake_profile.safety_concerns"],
                "routing": output_state["routing_decision"]
            }
        }
        
        return {
            "intake_profile": data,
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Intake Error: {e}")
        return {
            "intake_profile": {"intent": "GREETING", "error": str(e)},
            "agent_log": [{
                "agent": "Intake Specialist",
                "role": "Emotional Assessment & Intent Classification",
                "thought": f"Error during analysis: {str(e)[:50]}",
                "status": "failed",
                "input_state": input_state,
                "output_state": {"error": str(e)[:100]},
                "state_changes": {"added": [], "routing": "→ Care Manager (fallback)"}
            }]
        }


# ============================================================================
# AGENT 2: WEALTH ARCHITECT
# ============================================================================
WEALTH_PROMPT = """You are an Expert Financial Planner with 15+ years experience.
Analyze the user's financial situation and create a comprehensive plan.

OUTPUT ONLY VALID JSON:
{
  "financial_snapshot": {
    "monthly_income": "Amount or 'Unknown'",
    "monthly_expenses": "Estimated or stated",
    "current_cash_flow": "Positive/Negative/Neutral",
    "savings_rate": "Percentage if calculable"
  },
  "debt_analysis": {
    "total_debt": "Amount or 'Unknown'",
    "debt_types": [{"type": "Credit Card|Student Loan|Mortgage|Medical|Other", "amount": 0, "interest_rate": "if known", "priority": "High|Medium|Low"}],
    "debt_to_income_ratio": "Calculation or estimate",
    "recommended_strategy": "Avalanche|Snowball|Consolidation|Hybrid"
  },
  "assets_and_savings": {
    "emergency_fund": "Amount or status",
    "retirement_savings": "Amount if mentioned",
    "other_assets": "Any other assets mentioned"
  },
  "financial_health_score": 0-100,
  "major_challenges": ["Specific challenge 1", "Challenge 2"],
  "immediate_opportunities": ["Quick win 1", "Opportunity 2"],
  "detailed_strategy": {
    "phase_1_immediate": {
      "focus": "Main priority",
      "actions": ["Action 1", "Action 2"],
      "timeline": "1-4 weeks"
    },
    "phase_2_short_term": {
      "focus": "Next priority",
      "actions": ["Action 1", "Action 2"],
      "timeline": "1-3 months"
    },
    "phase_3_long_term": {
      "focus": "Future goals",
      "actions": ["Action 1"],
      "timeline": "3-12 months"
    }
  },
  "key_metrics_to_track": ["Metric 1", "Metric 2"]
}"""


async def run_financial_agent(state: MindMoneyState):
    """
    AGENT 2: Wealth Architect
    - Receives intake_profile from Agent 1
    - Only activates if intent == DATA_SUBMISSION
    - Produces comprehensive financial analysis
    """
    intake = state.get("intake_profile", {})
    intent = intake.get("intent", "GREETING")
    
    # =========== INPUT STATE ===========
    input_state = {
        "received_from": "Intake Specialist",
        "intent": intent,
        "anxiety_level": intake.get("emotional_state", {}).get("anxiety", 0),
        "user_input_preview": state['user_input'][:80] + "..." if len(state['user_input']) > 80 else state['user_input']
    }
    
    # Safety Check: Only run if we have financial data
    if intent != "DATA_SUBMISSION":
        return {
            "financial_profile": {},
            "agent_log": [{
                "agent": "Wealth Architect",
                "role": "Financial Analysis & Strategy",
                "thought": f"Skipped - Intent is '{intent}', not DATA_SUBMISSION. Waiting for user to provide financial details.",
                "status": "idle",
                "input_state": input_state,
                "output_state": {"skipped": True, "reason": "No financial data provided"},
                "state_changes": {"added": [], "routing": "→ Passed to Care Manager"}
            }]
        }

    settings = get_settings()
    client = get_gemini_client()
    
    # Include conversation history for context
    history_context = ""
    if state.get("conversation_history"):
        history_context = "\n".join([
            f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
            for msg in state["conversation_history"][-3:]
        ])
    
    context = f"{history_context}\nCURRENT MESSAGE: {state['user_input']}" if history_context else state['user_input']
    
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {WEALTH_PROMPT}\nUSER FINANCIAL SITUATION:\n{context}",
            config=types.GenerateContentConfig(
                temperature=settings.planner_temperature,
                response_mime_type="application/json"
            )
        )
        data = safe_parse_json(response.text)
        
        # Extract key metrics for logging
        health_score = data.get('financial_health_score', 0)
        total_debt = data.get('debt_analysis', {}).get('total_debt', 'Unknown')
        debt_types = data.get('debt_analysis', {}).get('debt_types', [])
        challenges = data.get('major_challenges', [])
        strategy = data.get('debt_analysis', {}).get('recommended_strategy', 'Unknown')
        
        # =========== OUTPUT STATE ===========
        output_state = {
            "health_score": health_score,
            "total_debt": total_debt,
            "debt_types_count": len(debt_types),
            "challenges_identified": len(challenges),
            "recommended_strategy": strategy,
            "phases_generated": list(data.get('detailed_strategy', {}).keys())
        }
        
        # =========== ENHANCED LOG ===========
        log = {
            "agent": "Wealth Architect",
            "role": "Financial Analysis & Strategy",
            "thought": f"Health Score: {health_score}/100 | Total Debt: {total_debt} | Strategy: {strategy} | Found {len(challenges)} challenges, {len(debt_types)} debt types",
            "status": "complete",
            "input_state": input_state,
            "output_state": output_state,
            "state_changes": {
                "added": ["financial_profile.health_score", "financial_profile.debt_analysis", "financial_profile.detailed_strategy"],
                "routing": "→ Care Manager (with financial context)"
            }
        }
        
        return {
            "financial_profile": data,
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Wealth Error: {e}")
        return {
            "financial_profile": {"error": str(e)},
            "agent_log": [{
                "agent": "Wealth Architect",
                "role": "Financial Analysis & Strategy",
                "thought": f"Error during analysis: {str(e)[:50]}",
                "status": "failed",
                "input_state": input_state,
                "output_state": {"error": str(e)[:100]},
                "state_changes": {"added": [], "routing": "→ Care Manager (without financial data)"}
            }]
        }


# ============================================================================
# AGENT 3: CARE MANAGER (The Context-Aware Synthesizer)
# ============================================================================

# Prompt for GREETING
CARE_PROMPT_GREETING = """You are MoneyBird, a compassionate AI financial wellness coach.
The user just greeted you or asked what you do. Introduce yourself warmly.
Keep response under 60 words. Be genuine, not salesy.
OUTPUT: Just the response text, no JSON."""

# Prompt for CLARIFICATION
CARE_PROMPT_CLARIFICATION = """You are MoneyBird, a compassionate financial wellness coach.
The user has shared a concern but hasn't provided specific details.
1. VALIDATE their feelings: {validation}
2. Ask for specific information: {missing_info}
Primary emotion: {primary_emotion} | Anxiety: {anxiety}/10
Keep under 80 words. Be warm, not clinical.
OUTPUT: Just the response text, no JSON."""

# Prompt for DATA_SUBMISSION with HIGH stress
CARE_PROMPT_STRESSED = """You are MoneyBird, a crisis de-escalation specialist.
User is highly stressed (anxiety {anxiety}/10, emotion: {primary_emotion}).
Validation to use: {validation}
Strategy from Wealth Architect: {strategy_summary}
1. Deep validation (2-3 sentences)
2. "## Your First Steps" header
3. 3 simple bullet points (easiest wins first)
4. Reassurance
NO jargon. Under 150 words.
OUTPUT: Markdown formatted response."""

# Prompt for MODERATE stress
CARE_PROMPT_MODERATE = """You are MoneyBird, a supportive financial coach.
User has moderate stress (anxiety {anxiety}/10, emotion: {primary_emotion}).
Health Score: {health_score}/100 | Challenges: {challenges}
Strategy: {strategy_summary}
1. Brief validation
2. "## Your Financial Snapshot" - 2-3 insights
3. "## Recommended Actions" - 3-4 steps
4. Encouraging close
Under 200 words.
OUTPUT: Markdown formatted response."""

# Prompt for CALM/optimizing
CARE_PROMPT_CALM = """You are MoneyBird, a strategic wealth coach.
User is calm and optimizing. Health Score: {health_score}/100
Challenges: {challenges}
Opportunities: {opportunities}
Strategy: {strategy}
1. "## Financial Health Assessment"
2. "## Optimization Strategy" (Immediate/Short/Long term)
3. "## Key Metrics to Track"
Professional tone.
OUTPUT: Markdown formatted response."""


async def run_synthesizer_agent(state: MindMoneyState):
    """
    AGENT 3: Care Manager
    - Receives intake_profile from Agent 1
    - Receives financial_profile from Agent 2 (if available)
    - Synthesizes empathetic, actionable response
    """
    settings = get_settings()
    client = get_gemini_client()
    
    intake = state.get("intake_profile") or {}
    wealth = state.get("financial_profile") or {}
    intent = intake.get("intent", "GREETING")
    
    # Get emotional data
    emotions = intake.get("emotional_state", {})
    anxiety = emotions.get("anxiety", 0)
    primary_emotion = emotions.get("primary_emotion", "neutral")
    validation = intake.get("validation_hook", "I hear you.")
    missing_info = intake.get("missing_info", [])
    
    # =========== INPUT STATE ===========
    input_state = {
        "received_from": ["Intake Specialist", "Wealth Architect"] if wealth else ["Intake Specialist"],
        "intent": intent,
        "anxiety_level": anxiety,
        "has_financial_profile": bool(wealth),
        "health_score": wealth.get("financial_health_score") if wealth else None,
        "validation_hook": validation[:50] + "..." if len(validation) > 50 else validation
    }
    
    # Determine style and build prompt
    if intent == "GREETING":
        prompt = CARE_PROMPT_GREETING
        context = f"USER MESSAGE: {state['user_input']}"
        style = "greeting"
        style_reason = "User sent a greeting/inquiry"
        
    elif intent == "CLARIFICATION":
        prompt = CARE_PROMPT_CLARIFICATION.format(
            primary_emotion=primary_emotion,
            anxiety=anxiety,
            validation=validation,
            missing_info=", ".join(missing_info) if missing_info else "income and debt details"
        )
        context = f"USER MESSAGE: {state['user_input']}"
        style = "clarification"
        style_reason = f"User needs to provide: {', '.join(missing_info[:2]) if missing_info else 'financial details'}"
        
    else:  # DATA_SUBMISSION
        health_score = wealth.get('financial_health_score', 50)
        challenges = wealth.get('major_challenges', [])
        opportunities = wealth.get('immediate_opportunities', [])
        strategy = wealth.get('detailed_strategy', {})
        
        if anxiety >= 7:
            prompt = CARE_PROMPT_STRESSED.format(
                anxiety=anxiety,
                primary_emotion=primary_emotion,
                validation=validation,
                strategy_summary=json.dumps(strategy.get('phase_1_immediate', {}), indent=2)
            )
            style = "crisis_support"
            style_reason = f"High anxiety ({anxiety}/10) - using calming approach"
            
        elif anxiety >= 4:
            prompt = CARE_PROMPT_MODERATE.format(
                primary_emotion=primary_emotion,
                anxiety=anxiety,
                health_score=health_score,
                challenges=", ".join(challenges[:3]) if challenges else "None identified",
                strategy_summary=json.dumps(strategy, indent=2)[:500]
            )
            style = "supportive_guidance"
            style_reason = f"Moderate anxiety ({anxiety}/10) - balanced approach"
            
        else:
            prompt = CARE_PROMPT_CALM.format(
                health_score=health_score,
                challenges=json.dumps(challenges, indent=2),
                opportunities=json.dumps(opportunities, indent=2),
                strategy=json.dumps(strategy, indent=2)
            )
            style = "strategic_optimization"
            style_reason = f"Low anxiety ({anxiety}/10) - optimization focus"
        
        context = f"USER MESSAGE: {state['user_input']}\nFINANCIAL ANALYSIS: {json.dumps(wealth, indent=2)[:1000]}"

    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {prompt}\n\nCONTEXT:\n{context}",
            config=types.GenerateContentConfig(
                temperature=settings.synthesizer_temperature
            )
        )
        
        final_text = response.text.strip() if response.text else "I'm here to help. Could you tell me more about your financial situation?"
        
        # =========== OUTPUT STATE ===========
        output_state = {
            "response_style": style,
            "style_reason": style_reason,
            "response_length": len(final_text),
            "used_financial_data": bool(wealth and intent == "DATA_SUBMISSION"),
            "emotional_calibration": f"Matched {primary_emotion} with {style} approach"
        }
        
        # =========== ENHANCED LOG ===========
        log = {
            "agent": "Care Manager",
            "role": "Empathetic Response Synthesis",
            "thought": f"Style: {style} | {style_reason}. Synthesized {len(final_text)} char response using {'financial analysis + ' if wealth else ''}emotional profile.",
            "status": "complete",
            "input_state": input_state,
            "output_state": output_state,
            "state_changes": {
                "added": ["final_response"],
                "routing": "→ Action Generator" if intent == "DATA_SUBMISSION" else "→ END (conversational)"
            }
        }
        
        return {
            "final_response": final_text,
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Synthesizer Error: {e}")
        return {
            "final_response": "I'm here to help with your finances. Could you share what's on your mind?",
            "agent_log": [{
                "agent": "Care Manager",
                "role": "Empathetic Response Synthesis",
                "thought": f"Error: {str(e)[:50]}",
                "status": "failed",
                "input_state": input_state,
                "output_state": {"error": str(e)[:100]},
                "state_changes": {"added": ["final_response (fallback)"], "routing": "→ END"}
            }]
        }


# ============================================================================
# AGENT 4: ACTION GENERATOR
# ============================================================================
ACTION_PROMPT = """You are a Financial Planning Specialist. 
Generate a JSON form schema and specific action items based on the financial strategy.

OUTPUT ONLY VALID JSON:
{
  "financial_planning_form": {
    "title": "Your Financial Action Plan",
    "description": "Track your progress with these action items"
  },
  "immediate_actions": [
    {
      "action": "Specific action description",
      "deadline": "This week|Next 2 weeks|This month",
      "difficulty": "easy|medium|hard",
      "expected_impact": "What this accomplishes",
      "category": "debt|savings|income|budgeting"
    }
  ],
  "quick_wins": ["Easy win 1", "Easy win 2"],
  "metrics_to_track": [
    {"name": "Metric name", "current": "Current value", "target": "Target value", "timeframe": "When"}
  ],
  "milestones": [
    {"milestone": "Description", "target_date": "Timeframe", "reward": "How to celebrate"}
  ]
}"""


async def run_action_generator(state: MindMoneyState):
    """
    AGENT 4: Action Generator
    - Receives financial_profile from Agent 2
    - Receives care context from Agent 3
    - Generates actionable plan items
    """
    intake = state.get("intake_profile", {})
    wealth = state.get("financial_profile", {})
    intent = intake.get("intent", "GREETING")
    
    # =========== INPUT STATE ===========
    input_state = {
        "received_from": ["Wealth Architect", "Care Manager"],
        "intent": intent,
        "has_financial_profile": bool(wealth),
        "health_score": wealth.get("financial_health_score") if wealth else None,
        "challenges_count": len(wealth.get("major_challenges", [])) if wealth else 0,
        "strategy_phases": list(wealth.get("detailed_strategy", {}).keys()) if wealth else []
    }
    
    # Early exit if no financial data
    if intent != "DATA_SUBMISSION":
        return {
            "action_plan": None,
            "agent_log": [{
                "agent": "Action Generator",
                "role": "Actionable Plan Creation",
                "thought": f"Skipped - Intent is '{intent}'. No action plan needed for conversational responses.",
                "status": "idle",
                "input_state": input_state,
                "output_state": {"skipped": True, "reason": "Non-financial conversation"},
                "state_changes": {"added": [], "routing": "→ END"}
            }]
        }

    settings = get_settings()
    client = get_gemini_client()
    
    context = f"""
FINANCIAL HEALTH SCORE: {wealth.get('financial_health_score', 'Unknown')}/100

STRATEGY:
{json.dumps(wealth.get('detailed_strategy', {}), indent=2)}

CHALLENGES:
{json.dumps(wealth.get('major_challenges', []), indent=2)}

OPPORTUNITIES:
{json.dumps(wealth.get('immediate_opportunities', []), indent=2)}
"""
    
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {ACTION_PROMPT}\nCONTEXT:\n{context}",
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        data = safe_parse_json(response.text)
        
        # Extract metrics for logging
        num_actions = len(data.get('immediate_actions', []))
        quick_wins = len(data.get('quick_wins', []))
        milestones = len(data.get('milestones', []))
        metrics = len(data.get('metrics_to_track', []))
        
        # =========== OUTPUT STATE ===========
        output_state = {
            "immediate_actions": num_actions,
            "quick_wins": quick_wins,
            "milestones": milestones,
            "metrics_to_track": metrics,
            "categories": list(set([a.get("category", "general") for a in data.get("immediate_actions", [])]))
        }
        
        # =========== ENHANCED LOG ===========
        log = {
            "agent": "Action Generator",
            "role": "Actionable Plan Creation",
            "thought": f"Generated {num_actions} actions, {quick_wins} quick wins, {milestones} milestones. Categories: {', '.join(output_state['categories'])}",
            "status": "complete",
            "input_state": input_state,
            "output_state": output_state,
            "state_changes": {
                "added": ["action_plan.immediate_actions", "action_plan.quick_wins", "action_plan.milestones", "action_plan.metrics"],
                "routing": "→ END (pipeline complete)"
            }
        }
        
        return {
            "action_plan": data,
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Action Generator Error: {e}")
        return {
            "action_plan": None,
            "agent_log": [{
                "agent": "Action Generator",
                "role": "Actionable Plan Creation",
                "thought": f"Error: {str(e)[:50]}",
                "status": "failed",
                "input_state": input_state,
                "output_state": {"error": str(e)[:100]},
                "state_changes": {"added": [], "routing": "→ END (with error)"}
            }]
        }


# ============================================================================
# AGENT 5: MARKET RESEARCHER (Optional - uses Tavily)
# ============================================================================
async def run_research_agent(state: MindMoneyState):
    """
    AGENT 5: Market Researcher
    - Runs in PARALLEL with Wealth Architect
    - Searches for relevant market data and resources
    - Only activates for DATA_SUBMISSION intent
    """
    intake = state.get("intake_profile", {})
    intent = intake.get("intent", "GREETING")
    
    # =========== INPUT STATE ===========
    input_state = {
        "received_from": "Intake Specialist (parallel with Wealth Architect)",
        "intent": intent,
        "trigger": "DATA_SUBMISSION detected" if intent == "DATA_SUBMISSION" else "N/A"
    }
    
    # Skip if no financial data
    if intent != "DATA_SUBMISSION":
        return {
            "market_data": "",
            "agent_log": [{
                "agent": "Market Researcher",
                "role": "External Data & Resources",
                "thought": f"Skipped - Intent is '{intent}'. Market research only for financial submissions.",
                "status": "idle",
                "input_state": input_state,
                "output_state": {"skipped": True},
                "state_changes": {"added": [], "routing": "→ Care Manager (parallel merge)"}
            }]
        }
    
    # Try to import and use Tavily if available
    try:
        from tools import perform_market_search
        
        wealth = state.get("financial_profile", {})
        debt_types = wealth.get("debt_analysis", {}).get("debt_types", [])
        
        # Create relevant search query
        if debt_types:
            primary_debt = debt_types[0].get("type", "debt")
            query = f"best strategies to pay off {primary_debt} 2024"
        else:
            query = "personal finance tips debt payoff strategies"
        
        search_results = perform_market_search(query)
        
        # =========== OUTPUT STATE ===========
        output_state = {
            "search_query": query,
            "results_found": bool(search_results),
            "data_type": "market_strategies"
        }
        
        return {
            "market_data": search_results,
            "agent_log": [{
                "agent": "Market Researcher",
                "role": "External Data & Resources",
                "thought": f"Searched: '{query}' - Found relevant market data and strategies",
                "status": "complete",
                "input_state": input_state,
                "output_state": output_state,
                "state_changes": {"added": ["market_data"], "routing": "→ Care Manager (parallel merge)"}
            }]
        }
        
    except ImportError:
        return {
            "market_data": "",
            "agent_log": [{
                "agent": "Market Researcher",
                "role": "External Data & Resources",
                "thought": "Search tools not configured (Tavily API key missing)",
                "status": "idle",
                "input_state": input_state,
                "output_state": {"skipped": True, "reason": "Tavily not configured"},
                "state_changes": {"added": [], "routing": "→ Care Manager (parallel merge)"}
            }]
        }
    except Exception as e:
        print(f"❌ Research Error: {e}")
        return {
            "market_data": "",
            "agent_log": [{
                "agent": "Market Researcher",
                "role": "External Data & Resources",
                "thought": f"Error: {str(e)[:50]}",
                "status": "failed",
                "input_state": input_state,
                "output_state": {"error": str(e)[:100]},
                "state_changes": {"added": [], "routing": "→ Care Manager (parallel merge)"}
            }]
        }