"""
workflow.py - The LangGraph Orchestrator
"""
import asyncio
from langgraph.graph import StateGraph, END
from schemas import MindMoneyState
from agents import run_intake_agent, run_financial_agent, run_synthesizer_agent

def create_graph():
    # 1. Initialize the Graph with our State Schema
    workflow = StateGraph(MindMoneyState)

    # 2. Add the "Workers" (Nodes)
    # These functions come from your agents.py
    workflow.add_node("intake_specialist", run_intake_agent)
    workflow.add_node("wealth_architect", run_financial_agent)
    workflow.add_node("care_manager", run_synthesizer_agent)

    # 3. Define the Flow (The Orchestration Logic)
    
    # PARALLEL EXECUTION: Both agents start immediately after user input
    workflow.set_entry_point("intake_specialist") 
    workflow.add_edge("intake_specialist", "care_manager")
    
    # We cheat slightly to make them run in parallel in LangGraph:
    # In a real async graph, we'd branch from start. 
    # For simplicity here, we chain them but logically they are separate tasks.
    # To truly parallelize in LangGraph, you map the entry point to multiple nodes.
    
    # BETTER PATTERN:
    # Start -> [Intake, Wealth] -> Care Manager
    
    # Let's redefine to support true parallel execution if you want "The Flex":
    workflow.set_entry_point("intake_specialist")
    workflow.set_entry_point("wealth_architect")
    
    # Both feed into the Synthesizer
    workflow.add_edge("intake_specialist", "care_manager")
    workflow.add_edge("wealth_architect", "care_manager")
    
    # Synthesizer is the end
    workflow.add_edge("care_manager", END)

    # 4. Compile
    return workflow.compile()

# Global instance
app_graph = create_graph()

async def run_mindmoney_workflow(user_input: str, history: list):
    """
    The main entry point called by the API.
    """
    # Initialize blank state
    initial_state = MindMoneyState(
        user_input=user_input,
        conversation_history=history,
        intake_profile={},
        financial_profile={},
        plan_draft={},
        strategy_decision={},
        final_response="",
        agent_log=[]
    )

    # Run the graph
    # LangGraph automatically handles passing state between nodes
    final_state = await app_graph.ainvoke(initial_state)
    
    return final_state