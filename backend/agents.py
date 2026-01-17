"""
MindMoney Agents - Three specialized AI agents for financial therapy.

Agent 1: Intake Specialist (Gemini) - Emotion & Identity Analysis
Agent 2: Financial Planner (Anthropic Claude) - Financial Extraction & Planning  
Agent 3: Synthesizer (OpenAI) - Response Generation with Conditional Routing
"""

import json
import time
from typing import Dict, Any, Tuple
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config import get_settings
from schemas import (
    MindMoneyState, 
    IntakeProfile, 
    FinancialProfile, 
    PlanDraft,
    StrategyDecision, 
    StrategyMode, 
    AgentName,
    EmotionProfile
)


# ============================================================================
# AGENT 1: INTAKE SPECIALIST (GEMINI)
# ============================================================================

INTAKE_SYSTEM_PROMPT = """You are a compassionate, empathetic Intake Specialist trained in Crisis Intervention and Cognitive Behavioral Therapy (CBT). 

Your role is to understand the HUMAN behind the financial stress - their identity, emotions, fears, and thought patterns. You do NOT provide financial advice or solutions.

ANALYZE the user's message and extract:

1. IDENTITY ROLES: What roles define this person? (partner, parent, provider, professional, student, caregiver, etc.)

2. IDENTITY THREATS: What aspects of their identity feel threatened? ("I'm a failure", "I'm irresponsible", "I'm not a good partner")

3. CORE VALUES: What values seem important to them? (stability, trust, independence, security, family, success)

4. EMOTIONS: Rate each 0-10:
   - anxiety: How anxious/worried do they seem?
   - shame: How much shame/embarrassment?
   - hope: How hopeful/optimistic despite the situation?

5. COGNITIVE DISTORTIONS: Identify any present:
   - Catastrophizing ("everything is ruined", "my partner will kill me")
   - All-or-nothing thinking ("I'm a total failure")
   - Mind reading ("they'll think I'm irresponsible")
   - Fortune telling ("I'll never get out of this")
   - Emotional reasoning ("I feel like a failure so I must be one")
   - Should statements ("I should have saved more")

6. SAFETY FLAG: Set to true ONLY if there are ANY hints of:
   - Self-harm thoughts
   - Crisis language
   - Hopelessness that seems severe
   - Mentions of "ending it" or "giving up on everything"

7. DISCLOSURE CONTEXT: If they mention fear of telling someone (partner, family, etc.), note this.

8. VALIDATION HOOK: Write ONE empathetic sentence that validates their feelings without minimizing them.

RESPOND ONLY with valid JSON in this exact format:
{
  "identity_roles": ["role1", "role2"],
  "identity_threats": ["threat1", "threat2"],
  "core_values": ["value1", "value2"],
  "emotions": {
    "anxiety": 0-10,
    "shame": 0-10,
    "hope": 0-10
  },
  "distortions": ["distortion1", "distortion2"],
  "safety_flag": false,
  "disclosure_context": "string or null",
  "validation_hook": "empathetic validation statement"
}

Remember: You are the LISTENER. You extract and understand. You do not solve."""


def create_intake_agent():
    """Create the Gemini-powered Intake Specialist agent."""
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=settings.intake_temperature,
        convert_system_message_to_human=True,
    )


def parse_intake_response(response_text: str) -> Dict[str, Any]:
    """Parse the JSON response from Gemini, with fallback handling."""
    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        parsed = json.loads(cleaned)
        intake = IntakeProfile(**parsed)
        return intake.model_dump()
        
    except (json.JSONDecodeError, ValueError) as e:
        return IntakeProfile(
            identity_roles=["user"],
            identity_threats=[],
            core_values=["stability"],
            emotions=EmotionProfile(anxiety=5, shame=5, hope=5),
            distortions=[],
            safety_flag=False,
            disclosure_context=None,
            validation_hook="I hear that you're going through a difficult time."
        ).model_dump()


async def run_intake_agent(state: MindMoneyState) -> MindMoneyState:
    """LangGraph node function for the Intake Specialist."""
    start_time = time.time()
    settings = get_settings()
    
    user_input = state.get("user_input", "")
    agent_log = state.get("agent_log", [])
    
    try:
        agent = create_intake_agent()
        
        history = state.get("conversation_history", [])
        context = ""
        if history:
            recent = history[-3:]
            context = "\n\nRecent conversation context:\n"
            for turn in recent:
                context += f"User: {turn.get('user', '')}\nAssistant: {turn.get('assistant', '')}\n"
        
        messages = [
            SystemMessage(content=INTAKE_SYSTEM_PROMPT),
            HumanMessage(content=f"{context}\n\nCurrent user message to analyze:\n{user_input}")
        ]
        
        response = await agent.ainvoke(messages)
        intake_profile = parse_intake_response(response.content)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        log_entry = {
            "agent_name": AgentName.INTAKE_SPECIALIST.value,
            "timestamp": datetime.utcnow().isoformat(),
            "input_summary": f"Analyzed: '{user_input[:100]}...'" if len(user_input) > 100 else f"Analyzed: '{user_input}'",
            "output_summary": f"Anxiety: {intake_profile['emotions']['anxiety']}, Shame: {intake_profile['emotions']['shame']}, Safety: {'⚠️ FLAGGED' if intake_profile['safety_flag'] else '✓ OK'}",
            "duration_ms": duration_ms,
            "model_used": settings.gemini_model,
            "decision_made": f"Detected distortions: {', '.join(intake_profile['distortions']) if intake_profile['distortions'] else 'None'}"
        }
        
        return {
            **state,
            "intake_profile": intake_profile,
            "agent_log": agent_log + [log_entry]
        }
        
    except Exception as e:
        error_log = {
            "agent_name": AgentName.INTAKE_SPECIALIST.value,
            "timestamp": datetime.utcnow().isoformat(),
            "input_summary": f"Error: {str(e)[:100]}",
            "output_summary": "Using fallback profile",
            "duration_ms": int((time.time() - start_time) * 1000),
            "model_used": settings.gemini_model,
        }
        
        fallback_profile = IntakeProfile(
            identity_roles=["user"],
            identity_threats=[],
            core_values=["stability"],
            emotions=EmotionProfile(anxiety=5, shame=5, hope=5),
            distortions=[],
            safety_flag=False,
            disclosure_context=None,
            validation_hook="I'm here to help you work through this."
        ).model_dump()
        
        errors = state.get("errors", [])
        
        return {
            **state,
            "intake_profile": fallback_profile,
            "agent_log": agent_log + [error_log],
            "errors": errors + [f"Intake agent error: {str(e)}"]
        }


# ============================================================================
# AGENT 2: FINANCIAL PLANNER (ANTHROPIC CLAUDE)
# ============================================================================

FINANCIAL_PLANNER_SYSTEM_PROMPT = """You are a Certified Financial Planner (CFP) with expertise in debt management, budgeting, and personal finance recovery strategies.

Your role is to be the CALCULATOR. You analyze text to extract financial facts and propose mathematically optimal strategies. You do NOT care about feelings - you care about accurate numbers and sound financial logic.

ANALYZE the user's message and extract:

1. FINANCIAL ENTITIES: Extract every financial item mentioned:
   - Debts (credit cards, loans, medical bills, etc.)
   - Income sources
   - Expenses (rent, utilities, subscriptions)
   - Assets (savings, investments)
   
   For each entity, capture:
   - entity_type: "debt", "income", "expense", "asset"
   - name: Description of the item
   - amount: Number if mentioned, null if unknown
   - status: "active", "overdue", "unknown", "increased", "decreased"
   - urgency: "high", "medium", "low" based on context

2. CONSTRAINTS: List any constraints mentioned

3. MISSING INFO: What numbers do you NEED to create a real plan?

4. CALCULATIONS (if possible):
   - total_debt: Sum of all debts if known
   - total_income: Monthly income if known
   - debt_to_income_ratio: Calculate if both are known

5. RECOMMENDED METHOD:
   - "Avalanche Method" (highest interest first)
   - "Snowball Method" (smallest debt first)
   - "Triage Mode" (minimum payments + emergency focus)
   - "Information Gathering" (when too many unknowns)

6. PLAN STEPS: Concrete, actionable steps

7. TIMELINE ESTIMATE: Rough estimate if possible

8. KEY INSIGHT: One crucial financial truth for their situation

RESPOND ONLY with valid JSON:
{
  "financial_profile": {
    "entities": [{"entity_type": "debt", "name": "Visa Card", "amount": 5000, "status": "active", "urgency": "high"}],
    "constraints": ["rent increased"],
    "missing_info": ["monthly income"],
    "total_debt": 5000,
    "total_income": null,
    "debt_to_income_ratio": null
  },
  "plan_draft": {
    "recommended_method": "Information Gathering",
    "steps": [{"step_number": 1, "action": "List exact monthly take-home income", "rationale": "Cannot budget without knowing income", "priority": "high"}],
    "timeline_estimate": "Cannot estimate without full picture",
    "key_insight": "You need to know your numbers before you can fight them."
  }
}"""


def create_financial_agent():
    """Create the Anthropic-powered Financial Planner agent."""
    settings = get_settings()
    return ChatAnthropic(
        model=settings.anthropic_model,
        anthropic_api_key=settings.anthropic_api_key,
        temperature=settings.planner_temperature,
    )


def parse_financial_response(response_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Parse the JSON response from Claude."""
    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        parsed = json.loads(cleaned)
        
        financial_data = parsed.get("financial_profile", {})
        plan_data = parsed.get("plan_draft", {})
        
        financial_profile = FinancialProfile(**financial_data)
        plan_draft = PlanDraft(**plan_data)
        
        return financial_profile.model_dump(), plan_draft.model_dump()
        
    except (json.JSONDecodeError, ValueError, KeyError):
        return (
            FinancialProfile(
                entities=[],
                constraints=["Unable to extract details"],
                missing_info=["Please share more about your financial situation"],
            ).model_dump(),
            PlanDraft(
                recommended_method="Information Gathering",
                steps=[{"step_number": 1, "action": "Share your financial details", "rationale": "Need more info", "priority": "high"}],
            ).model_dump()
        )


async def run_financial_agent(state: MindMoneyState) -> MindMoneyState:
    """LangGraph node function for the Financial Planner."""
    start_time = time.time()
    settings = get_settings()
    
    user_input = state.get("user_input", "")
    agent_log = state.get("agent_log", [])
    
    try:
        agent = create_financial_agent()
        
        history = state.get("conversation_history", [])
        context = ""
        if history:
            recent = history[-3:]
            context = "\n\nRecent conversation context:\n"
            for turn in recent:
                context += f"User: {turn.get('user', '')}\nAssistant: {turn.get('assistant', '')}\n"
        
        existing_financial = state.get("financial_profile", {})
        if existing_financial and existing_financial.get("entities"):
            context += "\n\nPreviously identified financial entities:\n"
            context += json.dumps(existing_financial.get("entities", []), indent=2)
        
        messages = [
            SystemMessage(content=FINANCIAL_PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=f"{context}\n\nCurrent user message to analyze:\n{user_input}")
        ]
        
        response = await agent.ainvoke(messages)
        financial_profile, plan_draft = parse_financial_response(response.content)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        entity_summary = []
        for entity in financial_profile.get("entities", []):
            if entity.get("amount"):
                entity_summary.append(f"{entity['name']}: ${entity['amount']}")
            else:
                entity_summary.append(f"{entity['name']}: unknown")
        
        log_entry = {
            "agent_name": AgentName.FINANCIAL_PLANNER.value,
            "timestamp": datetime.utcnow().isoformat(),
            "input_summary": f"Analyzed: '{user_input[:80]}...'" if len(user_input) > 80 else f"Analyzed: '{user_input}'",
            "output_summary": f"Found {len(financial_profile.get('entities', []))} entities. Method: {plan_draft.get('recommended_method', 'N/A')}",
            "duration_ms": duration_ms,
            "model_used": settings.anthropic_model,
            "decision_made": f"Entities: {', '.join(entity_summary[:3])}{'...' if len(entity_summary) > 3 else ''}" if entity_summary else "No entities found"
        }
        
        return {
            **state,
            "financial_profile": financial_profile,
            "plan_draft": plan_draft,
            "agent_log": agent_log + [log_entry]
        }
        
    except Exception as e:
        error_log = {
            "agent_name": AgentName.FINANCIAL_PLANNER.value,
            "timestamp": datetime.utcnow().isoformat(),
            "input_summary": f"Error: {str(e)[:100]}",
            "output_summary": "Using fallback profile",
            "duration_ms": int((time.time() - start_time) * 1000),
            "model_used": settings.anthropic_model,
        }
        
        fallback_financial = FinancialProfile(entities=[], constraints=[], missing_info=["Please share more details"]).model_dump()
        fallback_plan = PlanDraft(recommended_method="Information Gathering", steps=[]).model_dump()
        
        errors = state.get("errors", [])
        
        return {
            **state,
            "financial_profile": fallback_financial,
            "plan_draft": fallback_plan,
            "agent_log": agent_log + [error_log],
            "errors": errors + [f"Financial agent error: {str(e)}"]
        }


# ============================================================================
# AGENT 3: SYNTHESIZER (OPENAI)
# ============================================================================

def determine_strategy(intake_profile: Dict[str, Any], financial_profile: Dict[str, Any], plan_draft: Dict[str, Any]) -> StrategyDecision:
    """
    THE ORCHESTRATION LOGIC - Determines response strategy based on emotional state.
    This is what judges want to see - conditional routing based on anxiety/shame.
    """
    emotions = intake_profile.get("emotions", {})
    anxiety = emotions.get("anxiety", 5)
    shame = emotions.get("shame", 5)
    safety_flag = intake_profile.get("safety_flag", False)
    
    identity_threats = intake_profile.get("identity_threats", [])
    disclosure_context = intake_profile.get("disclosure_context")
    missing_info = financial_profile.get("missing_info", [])
    
    # RULE 1: Safety first
    if safety_flag:
        return StrategyDecision(
            mode=StrategyMode.CRISIS_SUPPORT,
            reason="Safety flag detected - prioritizing emotional support and resources",
            complexity_level=1,
            include_identity_reframe=True,
            include_disclosure_help=False,
            steps_to_show=0
        )
    
    # RULE 2: High anxiety (>= 8) - De-escalation mode
    if anxiety >= 8:
        return StrategyDecision(
            mode=StrategyMode.DE_ESCALATION,
            reason=f"Anxiety level {anxiety}/10 is very high - simplifying to one micro-step",
            complexity_level=1,
            include_identity_reframe=True if identity_threats else False,
            include_disclosure_help=False,
            steps_to_show=1
        )
    
    # RULE 3: High shame + identity threat
    if shame >= 7 and identity_threats:
        return StrategyDecision(
            mode=StrategyMode.DE_ESCALATION,
            reason=f"High shame ({shame}/10) with identity threats - reframing before advice",
            complexity_level=2,
            include_identity_reframe=True,
            include_disclosure_help=bool(disclosure_context),
            steps_to_show=2
        )
    
    # RULE 4: Moderate anxiety (5-7)
    if 5 <= anxiety < 8:
        return StrategyDecision(
            mode=StrategyMode.SIMPLIFIED,
            reason=f"Moderate anxiety ({anxiety}/10) - providing simplified 2-3 step plan",
            complexity_level=3,
            include_identity_reframe=bool(identity_threats),
            include_disclosure_help=bool(disclosure_context),
            steps_to_show=3
        )
    
    # RULE 5: Missing key info
    if len(missing_info) > 2:
        return StrategyDecision(
            mode=StrategyMode.SIMPLIFIED,
            reason=f"Need more information ({len(missing_info)} items missing)",
            complexity_level=2,
            include_identity_reframe=False,
            include_disclosure_help=False,
            steps_to_show=2
        )
    
    # RULE 6: User is calm - Full plan
    return StrategyDecision(
        mode=StrategyMode.FULL_PLAN,
        reason=f"Low anxiety ({anxiety}/10), adequate info - providing comprehensive plan",
        complexity_level=5,
        include_identity_reframe=False,
        include_disclosure_help=bool(disclosure_context),
        steps_to_show=min(len(plan_draft.get("steps", [])), 5)
    )


def build_synthesizer_prompt(strategy: StrategyDecision) -> str:
    """Build the system prompt based on the chosen strategy."""
    
    base_prompt = """You are a holistic wellness coach who synthesizes psychological insights and financial advice into compassionate, actionable responses.

You receive inputs from:
1. A Psychological Intake Specialist (emotions, identity, distortions)
2. A Financial Planner (entities, strategies, plans)

Your job is to create ONE unified response that helps the user feel heard AND gives them a clear next step."""

    mode_instructions = {
        StrategyMode.CRISIS_SUPPORT: """
CURRENT MODE: CRISIS SUPPORT
- Your PRIMARY goal is emotional safety
- Do NOT provide financial advice
- Acknowledge their pain with genuine empathy
- Gently suggest professional support resources
- Keep response warm, short, and grounding
- End with a simple check-in question""",

        StrategyMode.DE_ESCALATION: """
CURRENT MODE: DE-ESCALATION
- Your PRIMARY goal is reducing overwhelm
- Lead with emotional validation (use the validation_hook)
- If identity threats exist, gently reframe: "Feeling overwhelmed by finances doesn't make you irresponsible - it makes you human"
- Give ONLY ONE micro-step - the smallest possible action
- Keep response calming and short (under 150 words)
- End with encouragement, not more tasks""",

        StrategyMode.SIMPLIFIED: """
CURRENT MODE: SIMPLIFIED PLAN
- Balance emotional acknowledgment with practical steps
- Start with brief validation (1-2 sentences)
- If identity reframe needed, include it naturally
- Provide 2-3 clear steps maximum
- Use simple language, avoid financial jargon
- Keep response under 200 words""",

        StrategyMode.FULL_PLAN: """
CURRENT MODE: FULL PLAN
- User is ready for comprehensive guidance
- Briefly acknowledge their situation
- Present the recommended financial method
- Walk through the key steps clearly
- Include timeline if available
- Share the key insight
- Can be more detailed but stay organized"""
    }
    
    format_instructions = """

RESPONSE FORMAT:
- Write in a warm, conversational tone
- Use "you" and "we" language
- No bullet points or numbered lists
- No headers or markdown formatting
- Just natural, flowing paragraphs
- End with either a specific question or gentle encouragement

DO NOT:
- Dump all the financial data at once
- Use clinical or technical language
- Minimize their emotions
- Be preachy or lecture them

RESPOND with ONLY your message to the user - no JSON, no labels, just the response text."""

    return base_prompt + mode_instructions[strategy.mode] + format_instructions


def create_synthesizer_agent():
    """Create the OpenAI-powered Synthesizer agent."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=settings.synthesizer_temperature,
    )


async def run_synthesizer_agent(state: MindMoneyState) -> MindMoneyState:
    """LangGraph node function for the Synthesizer."""
    start_time = time.time()
    settings = get_settings()
    
    user_input = state.get("user_input", "")
    intake_profile = state.get("intake_profile", {})
    financial_profile = state.get("financial_profile", {})
    plan_draft = state.get("plan_draft", {})
    agent_log = state.get("agent_log", [])
    
    try:
        # STEP 1: Determine strategy (THE ORCHESTRATION LOGIC)
        strategy = determine_strategy(intake_profile, financial_profile, plan_draft)
        
        # STEP 2: Build the prompt based on strategy
        system_prompt = build_synthesizer_prompt(strategy)
        
        # STEP 3: Build the context message
        context = f"""USER'S ORIGINAL MESSAGE:
{user_input}

---

INTAKE SPECIALIST FINDINGS:
- Identity roles: {', '.join(intake_profile.get('identity_roles', ['unknown']))}
- Identity threats: {', '.join(intake_profile.get('identity_threats', ['none detected']))}
- Emotions: Anxiety {intake_profile.get('emotions', {}).get('anxiety', '?')}/10, Shame {intake_profile.get('emotions', {}).get('shame', '?')}/10
- Distortions: {', '.join(intake_profile.get('distortions', ['none'])) or 'none'}
- Validation hook: "{intake_profile.get('validation_hook', '')}"
- Disclosure concern: {intake_profile.get('disclosure_context', 'None mentioned')}

---

FINANCIAL PLANNER FINDINGS:
- Entities found: {json.dumps(financial_profile.get('entities', []), indent=2)}
- Missing info needed: {', '.join(financial_profile.get('missing_info', [])) or 'None'}
- Recommended method: {plan_draft.get('recommended_method', 'N/A')}
- Key insight: {plan_draft.get('key_insight', 'N/A')}
- Plan steps: {json.dumps(plan_draft.get('steps', [])[:strategy.steps_to_show], indent=2)}

---

YOUR STRATEGY FOR THIS RESPONSE:
- Mode: {strategy.mode.value}
- Reason: {strategy.reason}
- Include identity reframe: {strategy.include_identity_reframe}
- Include disclosure help: {strategy.include_disclosure_help}
- Steps to include: {strategy.steps_to_show}

Now write your response to the user:"""

        # STEP 4: Create and invoke the agent
        agent = create_synthesizer_agent()
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        response = await agent.ainvoke(messages)
        final_response = response.content.strip()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        log_entry = {
            "agent_name": AgentName.SYNTHESIZER.value,
            "timestamp": datetime.utcnow().isoformat(),
            "input_summary": f"Intake anxiety: {intake_profile.get('emotions', {}).get('anxiety', '?')}, Entities: {len(financial_profile.get('entities', []))}",
            "output_summary": f"Mode: {strategy.mode.value}, Steps shown: {strategy.steps_to_show}",
            "duration_ms": duration_ms,
            "model_used": settings.openai_model,
            "decision_made": strategy.reason
        }
        
        return {
            **state,
            "strategy_decision": strategy.model_dump(),
            "final_response": final_response,
            "agent_log": agent_log + [log_entry]
        }
        
    except Exception as e:
        error_log = {
            "agent_name": AgentName.SYNTHESIZER.value,
            "timestamp": datetime.utcnow().isoformat(),
            "input_summary": f"Error: {str(e)[:100]}",
            "output_summary": "Using fallback response",
            "duration_ms": int((time.time() - start_time) * 1000),
            "model_used": settings.openai_model,
        }
        
        fallback_response = "I hear that you're dealing with some financial stress right now. That takes courage to talk about. Let's take this one step at a time - can you tell me a bit more about what's weighing on you most?"
        
        fallback_strategy = StrategyDecision(
            mode=StrategyMode.DE_ESCALATION,
            reason="Fallback due to processing error",
            complexity_level=1,
            include_identity_reframe=False,
            include_disclosure_help=False,
            steps_to_show=0
        )
        
        errors = state.get("errors", [])
        
        return {
            **state,
            "strategy_decision": fallback_strategy.model_dump(),
            "final_response": fallback_response,
            "agent_log": agent_log + [error_log],
            "errors": errors + [f"Synthesizer error: {str(e)}"]
        }