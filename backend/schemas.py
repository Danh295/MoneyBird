"""
Pydantic models for MindMoney state management and API schemas.
"""

from typing import TypedDict, Any, List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class StrategyMode(str, Enum):
    DE_ESCALATION = "de_escalation"
    SIMPLIFIED = "simplified"
    FULL_PLAN = "full_plan"
    CRISIS_SUPPORT = "crisis_support"


class AgentName(str, Enum):
    INTAKE_SPECIALIST = "intake_specialist"
    FINANCIAL_PLANNER = "financial_planner"
    SYNTHESIZER = "synthesizer"


# ============================================================================
# Agent Output Models
# ============================================================================

class EmotionProfile(BaseModel):
    """Output from the Gemini Intake Specialist"""
    anxiety: int = Field(ge=0, le=10, description="Anxiety level 0-10")
    shame: int = Field(ge=0, le=10, description="Shame level 0-10")
    hope: int = Field(ge=0, le=10, description="Hope/optimism level 0-10")


class IntakeProfile(BaseModel):
    """Full intake profile from Gemini agent"""
    identity_roles: List[str] = Field(default_factory=list)
    identity_threats: List[str] = Field(default_factory=list)
    core_values: List[str] = Field(default_factory=list)
    emotions: EmotionProfile
    distortions: List[str] = Field(default_factory=list)
    safety_flag: bool = Field(default=False)
    disclosure_context: Optional[str] = Field(default=None)
    validation_hook: str = Field(default="")


class FinancialEntity(BaseModel):
    """A single financial entity extracted"""
    entity_type: str
    name: str
    amount: Optional[float] = None
    status: Optional[str] = None
    urgency: Optional[str] = None


class FinancialProfile(BaseModel):
    """Output from the Anthropic Financial Planner"""
    entities: List[FinancialEntity] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)
    total_debt: Optional[float] = None
    total_income: Optional[float] = None
    debt_to_income_ratio: Optional[float] = None


class PlanStep(BaseModel):
    """A single step in the financial plan"""
    step_number: int
    action: str
    rationale: str
    priority: str = "medium"


class PlanDraft(BaseModel):
    """Draft financial plan from Anthropic agent"""
    recommended_method: Optional[str] = None
    steps: List[PlanStep] = Field(default_factory=list)
    timeline_estimate: Optional[str] = None
    key_insight: Optional[str] = None


class StrategyDecision(BaseModel):
    """Decision made by the Synthesizer"""
    mode: StrategyMode
    reason: str
    complexity_level: int = Field(ge=1, le=5)
    include_identity_reframe: bool = False
    include_disclosure_help: bool = False
    steps_to_show: int = Field(ge=0, le=10)


class AgentLogEntry(BaseModel):
    """A single log entry from an agent execution"""
    agent_name: AgentName
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    input_summary: str
    output_summary: str
    duration_ms: Optional[int] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    decision_made: Optional[str] = None


# ============================================================================
# Main State Object (LangGraph TypedDict)
# ============================================================================

class MindMoneyState(TypedDict, total=False):
    """The main state object that flows through the LangGraph workflow."""
    session_id: str
    turn_number: int
    user_input: str
    conversation_history: List[Dict[str, str]]
    intake_profile: Dict[str, Any]
    financial_profile: Dict[str, Any]
    plan_draft: Dict[str, Any]
    strategy_decision: Dict[str, Any]
    final_response: str
    agent_log: List[Dict[str, Any]]
    errors: List[str]


# ============================================================================
# API Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Incoming chat request from frontend"""
    session_id: str
    message: str
    include_state: bool = True


class ChatResponse(BaseModel):
    """Final chat response to frontend"""
    session_id: str
    response: str
    state: Optional[Dict[str, Any]] = None
    agent_log: List[AgentLogEntry] = Field(default_factory=list)


class StateResponse(BaseModel):
    """Response for GET /state endpoint"""
    session_id: str
    state: Dict[str, Any]
    last_updated: datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    redis_connected: bool
    supabase_connected: bool


class SSEEventType(str, Enum):
    STATE_UPDATE = "state_update"
    AGENT_LOG = "agent_log"
    FINAL_RESPONSE = "final_response"
    ERROR = "error"
    STREAM_TOKEN = "stream_token"


class SSEEvent(BaseModel):
    """Server-Sent Event payload"""
    event_type: SSEEventType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)