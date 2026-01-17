# schemas.py
import operator
from typing import TypedDict, Any, List, Dict, Annotated
from pydantic import BaseModel

class MindMoneyState(TypedDict):
    # Shared Data
    user_input: str
    conversation_history: List[Dict[str, str]]
    
    # Agent Outputs
    intake_profile: Dict[str, Any]
    financial_profile: Dict[str, Any]
    market_data: str  # <--- NEW: Stores search results from Tavily
    
    # Final Results
    final_response: str
    action_plan: Dict[str, Any]
    
    # Logs (Append-only)
    agent_log: Annotated[List[Dict[str, Any]], operator.add]

# (ChatRequest and ChatResponse classes remain the same)
class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = [] 
    session_id: str = "demo-session"

class ChatResponse(BaseModel):
    response: str
    agent_logs: List[Dict[str, Any]]
    action_plan: Dict[str, Any] = {}