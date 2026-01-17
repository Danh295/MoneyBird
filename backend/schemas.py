"""
schemas.py - Fixed for Parallel Execution
"""
import operator
from typing import TypedDict, Any, List, Dict, Annotated
from pydantic import BaseModel

# --- The "Brain" State (LangGraph) ---
class MindMoneyState(TypedDict):
    # Shared Data (Read-Only for agents)
    user_input: str
    conversation_history: List[Dict[str, str]]
    
    # Agent Outputs (Specific to each agent)
    intake_profile: Dict[str, Any]
    financial_profile: Dict[str, Any]
    
    # Final Results
    final_response: str
    action_plan: Dict[str, Any]
    
    # LOGS: The Magic Fix
    # Annotated[list, operator.add] means "Append, don't Overwrite"
    # This allows multiple agents to write logs simultaneously without crashing.
    agent_log: Annotated[List[Dict[str, Any]], operator.add]

# --- API Request/Response (FastAPI) ---
class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = [] 
    session_id: str = "demo-session"

class ChatResponse(BaseModel):
    response: str
    agent_logs: List[Dict[str, Any]]
    action_plan: Dict[str, Any] = {}  # Optional action plan