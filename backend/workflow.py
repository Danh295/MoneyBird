# workflow.py
import asyncio
from langgraph.graph import StateGraph, START, END
from schemas import MindMoneyState
from agents import run_intake_agent, run_financial_agent, run_synthesizer_agent, run_action_generator, run_research_agent

def create_graph():
    # 1. Initialize Graph
    workflow = StateGraph(MindMoneyState)

    # 2. Add the "Workers"
    workflow.add_node("intake_specialist", run_intake_agent)
    workflow.add_node("wealth_architect", run_financial_agent)
    workflow.add_node("market_researcher", run_research_agent)
    workflow.add_node("care_manager", run_synthesizer_agent)
    workflow.add_node("action_generator", run_action_generator)

    # 3. Fan-Out (Parallel Start)
    # This fires both agents simultaneously
    workflow.add_edge(START, "intake_specialist")
    workflow.add_edge(START, "wealth_architect")
    workflow.add_edge(START, "market_researcher")

    # 4. Fan-In (Synchronization)
    # The Care Manager waits for BOTH upstream nodes to finish
    workflow.add_edge("intake_specialist", "care_manager")
    workflow.add_edge("wealth_architect", "care_manager")
    workflow.add_edge("market_researcher", "care_manager")

    # 5. Sequential Finish
    # Care Manager -> Action Generator -> End
    workflow.add_edge("care_manager", "action_generator")
    workflow.add_edge("action_generator", END)

    return workflow.compile()

app_graph = create_graph()

async def run_mindmoney_workflow(user_input: str, history: list):
    initial_state = MindMoneyState(
        user_input=user_input,
        conversation_history=history,
        intake_profile={},
        financial_profile={},
        market_data="",
        final_response="",
        action_plan={},
        agent_log=[]
    )
    
    # LangGraph handles the async parallel execution automatically here
    final_state = await app_graph.ainvoke(initial_state)
    return final_state