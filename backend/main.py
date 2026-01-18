"""
main.py - The API Entrypoint (Fixed History & Logs)
"""
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from schemas import ChatRequest, ChatResponse
from workflow import run_mindmoney_workflow
from supabase_logger import get_supabase_logger
import uvicorn

app = FastAPI(title="MindMoney API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. GET SESSIONS (Fixed Attribute Error) ---
@app.get("/api/sessions")
async def list_sessions(user_id: Optional[str] = Query(None)):
    """
    Fetch all unique sessions for a specific user.
    """
    logger = get_supabase_logger()
    # Correct method call matching the updated supabase_logger.py
    sessions = await logger.get_user_sessions(user_id)
    return {"sessions": sessions}

# --- 2. GET HISTORY ---
@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    logger = get_supabase_logger()
    try:
        history = await logger.get_session_history(session_id)
        
        formatted_history = []
        for turn in history:
            formatted_history.append({
                "id": f"{turn['id']}-user",
                "role": "user",
                "content": turn['user_message']
            })
            formatted_history.append({
                "id": f"{turn['id']}-ai",
                "role": "assistant",
                "content": turn['assistant_response'],
                "actionPlan": turn.get('state_snapshot', {}).get('action_plan')
            })
            
        return {"history": formatted_history}
    except Exception as e:
        print(f"History Error: {e}")
        return {"history": []}

# --- 3. CHAT ENDPOINT (Fixed User Tracking) ---
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Debug print to confirm user_id is arriving
    print(f"Received: {request.message} (Session: {request.session_id}) User: {request.user_id}")
    
    try:
        logger = get_supabase_logger()
        
        # 1. Fetch Context
        history_context = request.history
        if not history_context:
             db_history = await logger.get_session_history(request.session_id)
             for h in db_history:
                 history_context.append({"role": "user", "content": h['user_message']})
                 history_context.append({"role": "assistant", "content": h['assistant_response']})

        # 2. Run Workflow
        result_state = await run_mindmoney_workflow(
            user_input=request.message,
            history=history_context
        )
        
        # 3. Log to Supabase (WITH USER ID)
        logs = result_state.get("agent_log", [])
        
        await logger.log_conversation_turn(
            session_id=request.session_id,
            turn_number=(len(history_context) // 2) + 1,
            user_message=request.message,
            assistant_response=result_state["final_response"],
            state_snapshot=result_state,
            agent_logs=logs,
            user_id=request.user_id 
        )
        
        return ChatResponse(
            response=result_state["final_response"],
            agent_logs=logs,
            action_plan=result_state.get("action_plan", {})
        )
        
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)