"""
agents.py - Fixed Return Values & Model Name
"""
import json
import re
from typing import Dict, Any

from google import genai
from google.genai import types
from tools import perform_market_search

from dotenv import load_dotenv

from config import get_settings
from schemas import MindMoneyState

load_dotenv()

# --- SHARED CLIENT FACTORY ---
def get_gemini_client():
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)

def safe_parse_json(response_text: str | None) -> Dict[str, Any]:
    if not response_text: return {}
    try:
        text = re.sub(r'```json\s*', '', response_text)
        text = re.sub(r'```\s*', '', text)
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}

# ============================================================================
# AGENT 1: INTAKE SPECIALIST
# ============================================================================
INTAKE_PROMPT = """You are an Intake Specialist in financial wellness. Your role is to assess the user's emotional and psychological relationship with money.

ANALYZE THE USER'S MESSAGE AND OUTPUT ONLY VALID JSON:
{
  "emotional_state": {
    "anxiety": 0-10,
    "shame": 0-10,
    "overwhelm": 0-10,
    "hope": 0-10,
    "primary_emotion": "string"
  },
  "financial_psychology": {
    "money_beliefs": ["belief1", "belief2"],
    "avoidance_behaviors": ["behavior1", "behavior2"],
    "triggers": ["trigger1", "trigger2"]
  },
  "identity_threats": {
    "career_security": 0-10,
    "self_worth": 0-10,
    "family_stability": 0-10
  },
  "rapport_indicators": {
    "engagement_level": "low|medium|high",
    "barriers_to_openness": ["barrier1", "barrier2"],
    "trust_needed": ["validation", "competence", "confidentiality"]
  },
  "safety_concerns": {
    "crisis_flag": false,
    "escalation_needed": false
  },
  "validation_hook": "A compassionate, specific sentence validating their concern",
  "conversation_stage": "opening|exploring|deepening|planning"
}"""

async def run_intake_agent(state: MindMoneyState):
    settings = get_settings()
    client = get_gemini_client()
    
    # Build conversation context from history
    history_context = ""
    if state.get("conversation_history"):
        history_context = "\n".join([
            f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
            for msg in state["conversation_history"][-3:]  # Last 3 messages for context
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
        
        # Extract key metrics for logging
        emotions = data.get("emotional_state", {})
        primary = emotions.get("primary_emotion", "unknown")
        engagement = data.get("rapport_indicators", {}).get("engagement_level", "unknown")
        
        log = {
            "agent": "Intake Specialist", 
            "thought": f"Primary emotion: {primary} | Engagement: {engagement} | Anxiety: {emotions.get('anxiety', '?')}/10",
            "validation": data.get("validation_hook", ""),
            "status": "complete"
        }
        
        return {
            "intake_profile": data, 
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"Intake Error: {e}")
        return {
            "intake_profile": {"error": str(e)},
            "agent_log": [{"agent": "Intake Specialist", "thought": f"Error: {e}", "status": "failed"}]
        }

# ============================================================================
# AGENT 2: WEALTH ARCHITECT
# ============================================================================
WEALTH_PROMPT = """You are an Expert Financial Planner with 10+ years experience. Provide DETAILED financial analysis. Output ONLY valid JSON.

Analyze the user's financial situation comprehensively:
{
  "financial_snapshot": {
    "monthly_income": "Estimated or stated",
    "monthly_expenses": "Estimated or stated",
    "current_cash_flow": "Positive/Negative/Neutral",
    "savings_rate": "Percentage if calculable"
  },
  "debt_analysis": {
    "total_debt": "Amount or 'Unknown'",
    "debt_types": [{"type": "Credit Card|Student Loan|Mortgage|Medical", "amount": 0, "priority": "High|Medium|Low"}],
    "debt_to_income_ratio": "Calculation or estimate",
    "recommendations": ["Specific payoff strategy"]
  },
  "assets_and_savings": {
    "total_assets": "Amount or 'Unknown'",
    "emergency_fund_status": "3-6 months expenses recommended",
    "retirement_readiness": "Assessment"
  },
  "financial_health_score": 0-100,
  "major_challenges": ["Challenge with context"],
  "immediate_opportunities": ["Opportunity for improvement"],
  "detailed_strategy": {
    "primary_focus": "Main priority to address",
    "timeline": "Realistic timeframe",
    "action_steps": ["Detailed step 1", "Detailed step 2", "Detailed step 3"],
    "expected_outcomes": ["Outcome after 3 months", "Outcome after 6 months"]
  },
  "information_gaps": ["What we need to know to refine the plan"],
  "collaboration_with_therapist": "Any mental health factors that impact financial decisions?"
}"""

# agents.py

# ... (keep imports and Setup) ...

async def run_financial_agent(state: MindMoneyState):
    settings = get_settings()
    client = get_gemini_client()
    
    # --- PARALLEL EXECUTION FIX ---
    # We REMOVED 'intake_profile' here. 
    # The Wealth Architect is now "Blind" to emotions. It only sees the raw user text.
    # This ensures it doesn't crash waiting for the other agent.
    
    context = f"""
USER MESSAGE: {state['user_input']}
"""
    # Note: removed the "PSYCHOLOGICAL FACTORS" section from the context
    
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {WEALTH_PROMPT}\nCONTEXT:\n{context}",
            config=types.GenerateContentConfig(
                temperature=settings.planner_temperature,
                response_mime_type="application/json"
            )
        )
        data = safe_parse_json(response.text)
        
        challenges = data.get('major_challenges', [])
        opportunities = data.get('immediate_opportunities', [])
        
        log = {
            "agent": "Wealth Architect", 
            "thought": f"Health Score: {data.get('financial_health_score', '?')}/100 | Challenges: {len(challenges)} | Opportunities: {len(opportunities)}",
            "status": "complete"
        }
        
        return {
            "financial_profile": data, 
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Wealth Error: {e}")
        return {
            "financial_profile": {"error": str(e)},
            "agent_log": [{"agent": "Wealth Architect", "thought": f"Error: {e}", "status": "failed"}]
        }

# ============================================================================
# AGENT 3: CARE MANAGER (Response Synthesis)
# ============================================================================
CARE_PROMPT_STRESSED = """You are a Calm, Compassionate Wealth Coach speaking to a highly stressed person.

Guidelines:
- Start with VALIDATION of their emotion
- Keep sentences clear and direct
- Use warm, human tone
- Provide practical guidance
- End with actionable next steps

OUTPUT ONLY THE RESPONSE TEXT (no JSON)."""

CARE_PROMPT_MODERATE = """You are a Supportive Wealth Coach providing balanced, thoughtful guidance.

Guidelines:
- Lead with validation
- Provide key insights and context
- Share multiple actionable steps
- Keep it accessible and warm
- Be thorough but concise

OUTPUT ONLY THE RESPONSE TEXT (no JSON)."""

CARE_PROMPT_CALM = """You are a Strategic Wealth Coach providing comprehensive guidance.

Guidelines:
- Acknowledge their situation with depth
- Provide thorough insights and context
- Share multiple strategies and approaches
- Outline clear next steps with details
- Be professional, warm, and comprehensive

OUTPUT ONLY THE RESPONSE TEXT (no JSON)."""

async def run_synthesizer_agent(state: MindMoneyState):
    settings = get_settings()
    client = get_gemini_client()
    
    # Use .get() with defaults since parallel agents might have failed
    intake = state.get("intake_profile") or {}
    wealth = state.get("financial_profile") or {}
    
    # Determine stress level from intake data
    emotions = intake.get("emotional_state", {})
    anxiety = emotions.get("anxiety", 5)
    overwhelm = emotions.get("overwhelm", 5)
    stress_level = (anxiety + overwhelm) / 2
    
    # Select prompt based on stress
    if stress_level >= 7:
        care_prompt = CARE_PROMPT_STRESSED
        response_style = "stressed"
    elif stress_level >= 5:
        care_prompt = CARE_PROMPT_MODERATE
        response_style = "moderate"
    else:
        care_prompt = CARE_PROMPT_CALM
        response_style = "calm"
    
    context = f"""
USER MESSAGE: {state['user_input']}

PSYCHOLOGICAL STATE:
- Primary Emotion: {emotions.get('primary_emotion', 'unknown')}
- Anxiety: {anxiety}/10
- Overwhelm: {overwhelm}/10
- Engagement: {intake.get('rapport_indicators', {}).get('engagement_level', 'unknown')}

FINANCIAL CONTEXT:
{json.dumps(wealth.get('plan_draft', {}), indent=2)}

KEY VALIDATION: {intake.get('validation_hook', 'Your concerns matter.')}
"""
    
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {care_prompt}\nCONTEXT:{context}",
            config=types.GenerateContentConfig(
                temperature=settings.synthesizer_temperature
            )
        )
        
        final_text = response.text.strip() if response.text else "I'm here to help. Let's take this one step at a time."
        
        log = {
            "agent": "Care Manager", 
            "thought": f"Response synthesized for {response_style} stress level",
            "stress_level": f"{stress_level:.1f}/10",
            "response_length": len(final_text.split()),
            "status": "complete"
        }
        
        return {
            "final_response": final_text, 
            "agent_log": [log]
        }
        
    except Exception as e:
      error_msg = f"SYSTEM ERROR: {e} | Please try again later."
      print(f"❌ Synthesizer Error: {e}")
      return {
          "final_response": error_msg,
          "agent_log": [{"agent": "Care Manager", "thought": f"Error: {e}", "status": "failed"}]
      }

# ============================================================================
# AGENT 4: ACTION GENERATOR (Financial Planning Form & Action Steps)
# ============================================================================
ACTION_PROMPT = """You are a Financial Planning Specialist collaborating with the Wealth Architect. Generate a comprehensive financial information form and actionable next steps.

OUTPUT ONLY VALID JSON:
{
  "financial_planning_form": {
    "title": "Financial Planning Intake Form",
    "description": "Help us understand your situation better to create a personalized plan",
    "income_section": {
      "title": "Income Information",
      "fields": [
        {"name": "monthly_gross_income", "label": "Monthly Gross Income (before taxes)", "type": "number", "placeholder": "e.g., 5000", "required": true, "unit": "USD"},
        {"name": "other_income", "label": "Other Income Sources (freelance, side gigs)", "type": "text", "placeholder": "e.g., Freelance: $500/month", "required": false}
      ]
    },
    "expenses_section": {
      "title": "Monthly Expenses",
      "fields": [
        {"name": "housing", "label": "Housing (rent/mortgage/utilities)", "type": "number", "placeholder": "e.g., 1500", "required": true, "unit": "USD"},
        {"name": "food", "label": "Food & Groceries", "type": "number", "placeholder": "e.g., 400", "required": true, "unit": "USD"},
        {"name": "transportation", "label": "Transportation (car/transit)", "type": "number", "placeholder": "e.g., 300", "required": false, "unit": "USD"},
        {"name": "insurance", "label": "Insurance (health/auto/renter's)", "type": "number", "placeholder": "e.g., 250", "required": false, "unit": "USD"},
        {"name": "subscriptions", "label": "Subscriptions & Entertainment", "type": "number", "placeholder": "e.g., 50", "required": false, "unit": "USD"},
        {"name": "other_expenses", "label": "Other Regular Expenses", "type": "text", "placeholder": "List any other regular expenses", "required": false}
      ]
    },
    "debt_section": {
      "title": "Debt Information",
      "fields": [
        {"name": "credit_card", "label": "Total Credit Card Debt", "type": "number", "placeholder": "e.g., 3000", "required": false, "unit": "USD"},
        {"name": "student_loans", "label": "Student Loan Balance", "type": "number", "placeholder": "e.g., 25000", "required": false, "unit": "USD"},
        {"name": "auto_loan", "label": "Auto Loan Balance", "type": "number", "placeholder": "e.g., 15000", "required": false, "unit": "USD"},
        {"name": "mortgage", "label": "Mortgage Balance", "type": "number", "placeholder": "e.g., 250000", "required": false, "unit": "USD"},
        {"name": "other_debt", "label": "Other Debt (medical/personal)", "type": "text", "placeholder": "Type and amount", "required": false}
      ]
    },
    "savings_section": {
      "title": "Savings & Assets",
      "fields": [
        {"name": "emergency_fund", "label": "Emergency Fund / Savings", "type": "number", "placeholder": "e.g., 5000", "required": false, "unit": "USD"},
        {"name": "retirement", "label": "Retirement Savings (401k/IRA)", "type": "number", "placeholder": "e.g., 50000", "required": false, "unit": "USD"},
        {"name": "investments", "label": "Other Investments (stocks/bonds/crypto)", "type": "text", "placeholder": "Describe", "required": false}
      ]
    },
    "goals_section": {
      "title": "Financial Goals",
      "fields": [
        {"name": "primary_goal", "label": "What's your #1 financial priority?", "type": "select", "options": ["Pay off debt", "Build emergency fund", "Save for home", "Improve credit", "Invest for future", "Other"], "required": true},
        {"name": "timeline", "label": "Timeline for this goal?", "type": "select", "options": ["1-3 months", "3-6 months", "6-12 months", "1-2 years", "2+ years"], "required": false}
      ]
    }
  },
  "immediate_actions": [
    {"action": "Description", "deadline": "This week|Next 2 weeks|This month", "difficulty": "easy|medium|hard", "expected_impact": "What this accomplishes"}
  ],
  "quick_wins": ["Easy action to build momentum"],
  "next_steps": {
    "fill_form": "User should complete the financial form to provide missing data",
    "after_form": "Once form is completed, we can generate a detailed financial plan"
  }
}"""

async def run_action_generator(state: MindMoneyState):
    settings = get_settings()
    client = get_gemini_client()
    
    intake = state.get("intake_profile") or {}
    wealth = state.get("financial_profile") or {}
    
    context = f"""
USER MESSAGE: {state['user_input']}
FINANCIAL HEALTH SCORE: {wealth.get('financial_health_score', 'unknown')}/100

WEALTH ARCHITECT'S ANALYSIS:
{json.dumps(wealth.get('detailed_strategy', {}), indent=2)}

CHALLENGES IDENTIFIED:
{json.dumps(wealth.get('major_challenges', []))}

OPPORTUNITIES:
{json.dumps(wealth.get('immediate_opportunities', []))}

INFORMATION GAPS TO FILL:
{json.dumps(wealth.get('information_gaps', []))}

USER'S EMOTIONAL STATE: {intake.get('emotional_state', {}).get('primary_emotion', 'unknown')}
CAREER SECURITY: {intake.get('identity_threats', {}).get('career_security', '?')}/10
"""
    
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {ACTION_PROMPT}\nCONTEXT:\n{context}",
            config=types.GenerateContentConfig(
                temperature=0.3,  # Lower temp for consistency
                response_mime_type="application/json"
            )
        )
        data = safe_parse_json(response.text)
        
        form = data.get('financial_planning_form', {})
        total_fields = 0
        for section in ['income_section', 'expenses_section', 'debt_section', 'savings_section', 'goals_section']:
            total_fields += len(form.get(section, {}).get('fields', []))
        
        num_actions = len(data.get('immediate_actions', []))
        quick_wins = len(data.get('quick_wins', []))
        
        log = {
            "agent": "Action Generator", 
            "thought": f"Financial form with {total_fields} fields | {num_actions} actions | {quick_wins} quick wins | Collaborating with Wealth Architect",
            "status": "complete"
        }
        
        return {
            "action_plan": data,
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Action Generator Error: {e}")
        return {
            "action_plan": {"error": str(e)},
            "agent_log": [{"agent": "Action Generator", "thought": f"Error: {e}", "status": "failed"}]
        }
        
        
# ============================================================================
# AGENT: MARKET RESEARCHER (The "Tavily" Agent)
# ============================================================================
RESEARCH_PROMPT = """You are a Financial Research Assistant. Your job is to find REAL-WORLD resources.
Based on the user's input, generate a specific search query to find:
1. Interest rates (e.g., "current mortgage rates Ontario")
2. Financial products (e.g., "best balance transfer cards Canada")
3. Local support (e.g., "rent bank Waterloo", "free credit counseling Toronto")

Output ONLY the raw search query string. Nothing else."""

async def run_research_agent(state: MindMoneyState):
    settings = get_settings()
    client = get_gemini_client()
    
    try:
        # Step 1: Ask LLM what to search for
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {RESEARCH_PROMPT}\nUSER MESSAGE: {state['user_input']}",
        )
        
        if not response.text:
            raise ValueError("No response from LLM for research query.")
        else: query = response.text.strip()
        
        # Step 2: actually search the web
        search_results = perform_market_search(query)
        
        log = {
            "agent": "Market Researcher", 
            "thought": f"Searched for: '{query}'", 
            "status": "complete"
        }
        
        # Return the results so the Care Manager can see them
        return {
            "market_data": search_results, 
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Research Error: {e}")
        return {
            "market_data": "Search unavailable.",
            "agent_log": [{"agent": "Market Researcher", "thought": f"Error: {e}", "status": "failed"}]
        }
        