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
Extract entities:
{
  "entities": [{"item": "Name", "amount": 0, "type": "debt"}],
  "missing_info": ["income", "etc"],
  "plan_draft": {"strategy": "Name", "steps": ["1", "2"]}
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
            "thought": f"Found {len(data.get('entities', []))} entities",
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
# AGENT 3: CARE MANAGER
# ============================================================================
CARE_PROMPT = """You are a Holistic Wealth Coach.
Synthesize the reports below into a text response.
Rules:
1. Anxiety > 8: Focus on calm.
2. Anxiety < 5: Focus on plan.
"""

async def run_synthesizer_agent(state: MindMoneyState):
    settings = get_settings()
    client = get_gemini_client()
    
    # Use .get() with defaults since parallel agents might have failed
    intake = state.get("intake_profile") or {}
    wealth = state.get("financial_profile") or {}
    
    context = f"""
    USER: {state['user_input']}
    INTAKE: {json.dumps(intake)}
    WEALTH: {json.dumps(wealth)}
    """
    
    try:
        response = client.models.generate_content(
            model=settings.model_name,
            contents=f"SYSTEM: {CARE_PROMPT}\nCONTEXT: {context}",
            config=types.GenerateContentConfig(
                temperature=settings.synthesizer_temperature
            )
        )
        
        final_text = response.text if response.text else "System busy."
        
        log = {
            "agent": "Care Manager", 
            "thought": "Response synthesized.", 
            "status": "complete"
        }
        
        return {
            "final_response": final_text, 
            "agent_log": [log]
        }
        
    except Exception as e:
        print(f"❌ Synthesizer Error: {e}")
        return {"final_response": "System Error."}