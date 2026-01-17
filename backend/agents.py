"""
agents.py - Fixed Return Values & Model Name
"""
import json
import re
from typing import Dict, Any

from google import genai
from google.genai import types

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
        print(f"❌ Intake Error: {e}")
        return {
            "intake_profile": {"error": str(e)},
            "agent_log": [{"agent": "Intake Specialist", "thought": f"Error: {e}", "status": "failed"}]
        }

# ============================================================================
# AGENT 2: WEALTH ARCHITECT
# ============================================================================
WEALTH_PROMPT = """You are a Financial Planner. Output ONLY valid JSON.
Extract entities and generate a structured plan:
{
  "entities": [{"item": "Name", "amount": 0, "type": "debt|asset|income"}],
  "missing_info": ["income", "expenses", "savings"],
  "financial_health_score": 0-100,
  "priority_areas": ["area1", "area2"],
  "plan_draft": {
    "strategy": "Strategic Name",
    "timeline_weeks": 4-12,
    "steps": ["Step 1 with detail", "Step 2 with detail"]
  }
}"""

async def run_financial_agent(state: MindMoneyState):
    settings = get_settings()
    client = get_gemini_client()
    
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {WEALTH_PROMPT}\nUSER: {state['user_input']}",
            config=types.GenerateContentConfig(
                temperature=settings.planner_temperature,
                response_mime_type="application/json"
            )
        )
        data = safe_parse_json(response.text)
        
        log = {
            "agent": "Wealth Architect", 
            "thought": f"Found {len(data.get('entities', []))} entities | Health Score: {data.get('financial_health_score', '?')}/100",
            "status": "complete"
        }
        
        # FIX: ONLY return new data
        return {
            "financial_profile": data, 
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Wealth Error: {e}")
        return {"agent_log": [{"agent": "Wealth Architect", "thought": f"Error: {e}"}]}

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
        print(f"❌ Synthesizer Error: {e}")
        return {"final_response": "I'm here to support you. What would help most right now?"}

# ============================================================================
# AGENT 4: ACTION GENERATOR (Actionable Steps & Resources)
# ============================================================================
ACTION_PROMPT = """You are an Action Planning Specialist. Generate concrete, actionable next steps.

OUTPUT ONLY VALID JSON:
{
  "immediate_actions": [
    {
      "action": "Specific action description",
      "deadline": "timeframe (e.g., 'This week', 'Next 2 weeks')",
      "difficulty": "easy|medium|hard",
      "resources_needed": ["resource1", "resource2"]
    }
  ],
  "information_needed_form": {
    "title": "What we need to know",
    "fields": [
      {
        "name": "field_name",
        "label": "User-friendly label",
        "type": "text|number|select|date",
        "placeholder": "Example or hint",
        "required": true|false
      }
    ]
  },
  "resources": {
    "therapy_resources": ["Resource type: Description or link"],
    "financial_tools": ["Tool name: What it does"],
    "educational_materials": ["Topic: Link or description"]
  },
  "support_contacts": {
    "crisis_hotline": "Phone number and description",
    "financial_counseling": "Organization: Phone/Email",
    "therapy_finder": "How to find local therapists"
  },
  "budget_template": {
    "categories": ["Income", "Fixed Expenses", "Variable Expenses", "Savings"],
    "suggested_percentages": {"Housing": 30, "Food": 15, "Transport": 10}
  }
}"""

async def run_action_generator(state: MindMoneyState):
    settings = get_settings()
    client = get_gemini_client()
    
    intake = state.get("intake_profile") or {}
    wealth = state.get("financial_profile") or {}
    
    context = f"""
USER: {state['user_input']}
FINANCIAL HEALTH: {wealth.get('financial_health_score', 'unknown')}/100
PRIORITY AREAS: {json.dumps(wealth.get('priority_areas', []))}
MISSING INFO: {json.dumps(wealth.get('missing_info', []))}
EMOTIONAL STATE: {json.dumps(intake.get('emotional_state', {}))}
"""
    
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {ACTION_PROMPT}\nCONTEXT:\n{context}",
            config=types.GenerateContentConfig(
                temperature=0.4,  # Lower temp for consistency
                response_mime_type="application/json"
            )
        )
        data = safe_parse_json(response.text)
        
        num_actions = len(data.get('immediate_actions', []))
        form_fields = len(data.get('information_needed_form', {}).get('fields', []))
        
        log = {
            "agent": "Action Generator", 
            "thought": f"Generated {num_actions} immediate actions | {form_fields} form fields",
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