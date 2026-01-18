# schemas.py
import operator
from typing import TypedDict, Any, List, Dict, Annotated, Optional
from pydantic import BaseModel


def merge_dicts(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Simple merger to ensure dictionary updates don't overwrite previous keys."""
    if not existing:
        return new
    if not new:
        return existing
    updated = existing.copy()
    updated.update(new)
    return updated


class MindMoneyState(TypedDict):
    # Shared Data
    user_input: str
    conversation_history: List[Dict[str, str]]
    
    # Agent Outputs
    intake_profile: Annotated[Dict[str, Any], merge_dicts]
    financial_profile: Annotated[Dict[str, Any], merge_dicts]
    market_data: str
    
    # Final Results
    final_response: str
    action_plan: Optional[Dict[str, Any]]
    
    # Logs (Append-only)
    agent_log: Annotated[List[Dict[str, Any]], operator.add]


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    session_id: str = "demo-session"
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    agent_logs: List[Dict[str, Any]]
    action_plan: Optional[Dict[str, Any]] = None