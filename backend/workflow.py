# workflow.py
import asyncio
from typing import Literal

from langgraph.graph import StateGraph, START, END
from schemas import MindMoneyState

from agents import (
    run_intake_agent,
    run_financial_agent,
    run_research_agent,
    run_synthesizer_agent,
    run_action_generator
)


# ============================================================================
# PARALLEL ANALYSIS NODE
# ============================================================================
async def run_parallel_analysis(state: MindMoneyState):
    """
    Runs Wealth Architect and Market Researcher in parallel.
    Only called when intent is DATA_SUBMISSION.
    """
    print("Running parallel financial analysis...")
    
    # Run both agents concurrently
    wealth_result, research_result = await asyncio.gather(
        run_financial_agent(state),
        run_research_agent(state)
    )
    
    # Merge results
    return {
        "financial_profile": wealth_result.get("financial_profile", {}),
        "market_data": research_result.get("market_data", ""),
        "agent_log": wealth_result.get("agent_log", []) + research_result.get("agent_log", [])
    }


# ============================================================================
# ROUTING LOGIC
# ============================================================================
def route_after_intake(state: MindMoneyState) -> Literal["analyze", "converse"]:
    """
    Decides the path based on the 'intent' from Intake Specialist.
    """
    intent = state.get("intake_profile", {}).get("intent", "GREETING")
    
    print(f"ROUTER: Intent = '{intent}'")

    if intent == "DATA_SUBMISSION":
        print("   → Taking ANALYSIS path (Wealth + Research)")
        return "analyze"
    else:
        print("   → Taking CONVERSATION path (Skip to Care Manager)")
        return "converse"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================
def create_graph():
    """
    Creates the LangGraph workflow with conditional routing.
    
    Flow:
    START → Intake Specialist → [ROUTER]
                                    ├─ DATA_SUBMISSION → Parallel Analysis → Care Manager → Action Generator → END
                                    └─ GREETING/CLARIFICATION → Care Manager → Action Generator → END
    """
    workflow = StateGraph(MindMoneyState)

    # 1. Add all nodes
    workflow.add_node("intake_specialist", run_intake_agent)
    workflow.add_node("parallel_analysis", run_parallel_analysis)
    workflow.add_node("care_manager", run_synthesizer_agent)
    workflow.add_node("action_generator", run_action_generator)

    # 2. Entry point
    workflow.add_edge(START, "intake_specialist")

    # 3. Conditional routing after intake
    workflow.add_conditional_edges(
        "intake_specialist",
        route_after_intake,
        {
            "analyze": "parallel_analysis",   # Has financial data
            "converse": "care_manager"        # No data yet, just chat
        }
    )

    # 4. After parallel analysis, go to care manager
    workflow.add_edge("parallel_analysis", "care_manager")

    # 5. Care manager → Action generator → END
    workflow.add_edge("care_manager", "action_generator")
    workflow.add_edge("action_generator", END)

    return workflow.compile()


# ============================================================================
# GRAPH INSTANCE & RUNNER
# ============================================================================
app_graph = create_graph()


async def run_mindmoney_workflow(user_input: str, history: list) -> MindMoneyState:
    """
    Main entry point to run the MindMoney workflow.
    
    Args:
        user_input: The user's message
        history: List of previous messages [{"role": "user"|"assistant", "content": "..."}]
    
    Returns:
        Final state with all agent outputs
    """
    print(f"\n{'='*60}")
    print(f"MINDMONEY WORKFLOW START")
    print(f"Input: {user_input[:100]}...")
    print(f"{'='*60}\n")
    
    initial_state: MindMoneyState = {
        "user_input": user_input,
        "conversation_history": history,
        "intake_profile": {},
        "financial_profile": {},
        "market_data": "",
        "final_response": "",
        "action_plan": None,
        "agent_log": []
    }
    
    try:
        final_state = await app_graph.ainvoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"WORKFLOW COMPLETE")
        print(f"   Agents run: {len(final_state.get('agent_log', []))}")
        print(f"   Response length: {len(final_state.get('final_response', ''))}")
        print(f"{'='*60}\n")
        
        return final_state
        
    except Exception as e:
        print(f"Workflow error: {e}")
        # Return a safe fallback state
        return {
            **initial_state,
            "final_response": "I apologize, but I encountered an error. Could you try rephrasing your message?",
            "agent_log": [{"agent": "System", "thought": f"Workflow error: {e}", "status": "failed"}]
        }