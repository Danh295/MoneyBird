# agents.py
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
    settings = get_settings()
    client = get_gemini_client()
    
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
        
        # Default to GREETING if parsing fails
        intent = data.get("intent", "GREETING")
        emotions = data.get("emotional_state", {})
        primary_emotion = emotions.get("primary_emotion", "neutral")
        anxiety = emotions.get("anxiety", 0)
        
        log = {
            "agent": "Intake Specialist",
            "thought": f"Intent: {intent} | Emotion: {primary_emotion} | Anxiety: {anxiety}/10",
            "status": "complete"
        }
        
        return {
            "intake_profile": data,
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Intake Error: {e}")
        return {
            "intake_profile": {"intent": "GREETING", "error": str(e)},
            "agent_log": [{"agent": "Intake Specialist", "thought": f"Error: {e}", "status": "failed"}]
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
    # Safety Check: Only run if we have financial data
    intake = state.get("intake_profile", {})
    if intake.get("intent") != "DATA_SUBMISSION":
        return {
            "financial_profile": {},
            "agent_log": [{"agent": "Wealth Architect", "thought": "Skipped (no financial data)", "status": "idle"}]
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
        
        health_score = data.get('financial_health_score', '?')
        challenges = len(data.get('major_challenges', []))
        
        return {
            "financial_profile": data,
            "agent_log": [{"agent": "Wealth Architect", "thought": f"Health Score: {health_score}/100 | {challenges} challenges identified", "status": "complete"}]
        }
    except Exception as e:
        print(f"❌ Wealth Error: {e}")
        return {
            "financial_profile": {"error": str(e)},
            "agent_log": [{"agent": "Wealth Architect", "thought": f"Error: {e}", "status": "failed"}]
        }


# ============================================================================
# AGENT 3: CARE MANAGER (The Context-Aware Synthesizer)
# ============================================================================

# Prompt for GREETING - User just said hi or asked what this is
CARE_PROMPT_GREETING = """You are MindMoney, a compassionate AI financial wellness coach.

The user just greeted you or asked what you do. Introduce yourself warmly and invite them to share their financial situation.

RESPONSE REQUIREMENTS:
1. Be warm and welcoming (1-2 sentences)
2. Briefly explain what you do: "I help people understand their finances and create personalized plans to reduce stress and build wealth."
3. Ask an open-ended question to get them started

EXAMPLES OF GOOD OPENING QUESTIONS:
- "What's on your mind when it comes to money lately?"
- "Is there a financial goal you're working toward, or a challenge that's been weighing on you?"
- "How are you feeling about your finances right now?"

Keep total response under 60 words. Be genuine, not salesy.
OUTPUT: Just the response text, no JSON."""

# Prompt for CLARIFICATION - User mentioned a problem but no specifics
CARE_PROMPT_CLARIFICATION = """You are MindMoney, a compassionate financial wellness coach.

The user has shared a financial concern but hasn't provided specific details yet. Your job is to:
1. VALIDATE their feelings first (use the validation hook provided)
2. Ask for the SPECIFIC information we need to help them

CONTEXT:
- User's primary emotion: {primary_emotion}
- Anxiety level: {anxiety}/10
- Validation hook to use: {validation}
- Information we need: {missing_info}

RESPONSE FORMAT:
1. Start with empathy/validation (acknowledge their feelings)
2. Explain briefly why the details help: "To give you a personalized strategy..."
3. Ask for 1-2 specific pieces of information naturally

EXAMPLE:
"I hear you - dealing with debt can feel really overwhelming, and it takes courage to even talk about it. To create a plan that actually works for your situation, it would help to know a bit more. Could you share roughly how much debt you're dealing with and your approximate monthly income?"

Keep response under 80 words. Be warm, not clinical.
OUTPUT: Just the response text, no JSON."""

# Prompt for DATA_SUBMISSION with HIGH stress
CARE_PROMPT_STRESSED = """You are MindMoney, a crisis de-escalation specialist for financial wellness.

The user is highly stressed (anxiety {anxiety}/10). Your priority is to CALM them down first, then provide guidance.

CONTEXT:
- User's emotion: {primary_emotion}
- Validation: {validation}
- Financial Plan Summary: {strategy_summary}

RESPONSE STRUCTURE:
1. **Deep Validation** (2-3 sentences acknowledging their stress)
2. **"## Your First Steps"** header
3. **3 simple, concrete bullet points** from the financial plan (easiest wins first)
4. **Reassurance** (1 sentence: "We'll tackle this together, one step at a time.")

RULES:
- NO jargon or complex financial terms
- NO overwhelming lists
- Focus on what they can do THIS WEEK
- Under 150 words total

OUTPUT: Markdown formatted response."""

# Prompt for DATA_SUBMISSION with MODERATE stress
CARE_PROMPT_MODERATE = """You are MindMoney, a supportive financial wellness coach.

The user has moderate stress and has shared financial details. Provide balanced guidance.

CONTEXT:
- User's emotion: {primary_emotion}
- Anxiety level: {anxiety}/10
- Financial Health Score: {health_score}/100
- Key Challenges: {challenges}
- Strategy Summary: {strategy_summary}

RESPONSE STRUCTURE:
1. **Brief validation** (1-2 sentences)
2. **"## Your Financial Snapshot"** - 2-3 key insights
3. **"## Recommended Actions"** - 3-4 prioritized steps
4. **Encouraging close** (1 sentence)

Keep under 200 words. Balance empathy with actionable advice.
OUTPUT: Markdown formatted response."""

# Prompt for DATA_SUBMISSION with LOW stress (calm/optimizing)
CARE_PROMPT_CALM = """You are MindMoney, a strategic wealth optimization coach.

The user is relatively calm and looking to optimize. Provide comprehensive, professional guidance.

CONTEXT:
- Financial Health Score: {health_score}/100
- Key Challenges: {challenges}
- Opportunities: {opportunities}
- Full Strategy: {strategy}

RESPONSE STRUCTURE:
1. **"## Financial Health Assessment"** - Score and key metrics
2. **"## Optimization Strategy"**
   - **Immediate** (This month)
   - **Short-term** (1-3 months)
   - **Long-term** (3-12 months)
3. **"## Key Metrics to Track"** - What to monitor

Be thorough but organized. Use professional tone.
OUTPUT: Markdown formatted response."""


async def run_synthesizer_agent(state: MindMoneyState):
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
    
    # Determine which prompt to use based on intent and stress level
    if intent == "GREETING":
        prompt = CARE_PROMPT_GREETING
        context = f"USER MESSAGE: {state['user_input']}"
        style = "greeting"
        
    elif intent == "CLARIFICATION":
        prompt = CARE_PROMPT_CLARIFICATION.format(
            primary_emotion=primary_emotion,
            anxiety=anxiety,
            validation=validation,
            missing_info=", ".join(missing_info) if missing_info else "income and debt details"
        )
        context = f"USER MESSAGE: {state['user_input']}"
        style = "clarification"
        
    else:  # DATA_SUBMISSION
        # Get financial data for context
        health_score = wealth.get('financial_health_score', 50)
        challenges = wealth.get('major_challenges', [])
        opportunities = wealth.get('immediate_opportunities', [])
        strategy = wealth.get('detailed_strategy', {})
        
        # Select prompt based on anxiety level
        if anxiety >= 7:
            prompt = CARE_PROMPT_STRESSED.format(
                anxiety=anxiety,
                primary_emotion=primary_emotion,
                validation=validation,
                strategy_summary=json.dumps(strategy.get('phase_1_immediate', {}), indent=2)
            )
            style = "stressed"
            
        elif anxiety >= 4:
            prompt = CARE_PROMPT_MODERATE.format(
                primary_emotion=primary_emotion,
                anxiety=anxiety,
                health_score=health_score,
                challenges=", ".join(challenges[:3]) if challenges else "None identified",
                strategy_summary=json.dumps(strategy, indent=2)[:500]
            )
            style = "moderate"
            
        else:
            prompt = CARE_PROMPT_CALM.format(
                health_score=health_score,
                challenges=json.dumps(challenges, indent=2),
                opportunities=json.dumps(opportunities, indent=2),
                strategy=json.dumps(strategy, indent=2)
            )
            style = "calm"
        
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
        
        return {
            "final_response": final_text,
            "agent_log": [{"agent": "Care Manager", "thought": f"Style: {style} | Anxiety: {anxiety}/10", "status": "complete"}]
        }
        
    except Exception as e:
        print(f"❌ Synthesizer Error: {e}")
        return {
            "final_response": "I'm here to help with your finances. Could you share what's on your mind?",
            "agent_log": [{"agent": "Care Manager", "thought": f"Error: {e}", "status": "failed"}]
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
    intake = state.get("intake_profile", {})
    
    # Early exit if no financial data
    if intake.get("intent") != "DATA_SUBMISSION":
        return {
            "action_plan": None,
            "agent_log": [{"agent": "Action Generator", "thought": "Skipped (no financial data)", "status": "idle"}]
        }

    settings = get_settings()
    client = get_gemini_client()
    wealth = state.get("financial_profile") or {}
    
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
        
        num_actions = len(data.get('immediate_actions', []))
        
        return {
            "action_plan": data,
            "agent_log": [{"agent": "Action Generator", "thought": f"Generated {num_actions} action items", "status": "complete"}]
        }
        
    except Exception as e:
        print(f"❌ Action Generator Error: {e}")
        return {
            "action_plan": None,
            "agent_log": [{"agent": "Action Generator", "thought": f"Error: {e}", "status": "failed"}]
        }


# ============================================================================
# AGENT 5: MARKET RESEARCHER (Optional - uses Tavily)
# ============================================================================
async def run_research_agent(state: MindMoneyState):
    """
    Searches for relevant market data, rates, or resources.
    Only runs when we have financial data to contextualize.
    """
    intake = state.get("intake_profile", {})
    
    # Skip if no financial data
    if intake.get("intent") != "DATA_SUBMISSION":
        return {
            "market_data": "",
            "agent_log": [{"agent": "Market Researcher", "thought": "Skipped (no financial context)", "status": "idle"}]
        }
    
    # Try to import and use Tavily if available
    try:
        from tools import perform_market_search
        
        settings = get_settings()
        client = get_gemini_client()
        
        # Generate a search query based on user's situation
        wealth = state.get("financial_profile", {})
        debt_types = wealth.get("debt_analysis", {}).get("debt_types", [])
        
        # Create relevant search query
        if debt_types:
            primary_debt = debt_types[0].get("type", "debt")
            query = f"best strategies to pay off {primary_debt} 2024"
        else:
            query = "personal finance tips debt payoff strategies"
        
        search_results = perform_market_search(query)
        
        return {
            "market_data": search_results,
            "agent_log": [{"agent": "Market Researcher", "thought": f"Searched: '{query}'", "status": "complete"}]
        }
        
    except ImportError:
        # Tavily not configured, skip gracefully
        return {
            "market_data": "",
            "agent_log": [{"agent": "Market Researcher", "thought": "Search tools not configured", "status": "idle"}]
        }
    except Exception as e:
        print(f"❌ Research Error: {e}")
        return {
            "market_data": "",
            "agent_log": [{"agent": "Market Researcher", "thought": f"Error: {e}", "status": "failed"}]
        }