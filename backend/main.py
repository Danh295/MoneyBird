"""
main.py - The API Entrypoint (Fixed for Compatibility)
"""
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header, Depends
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

# ============================================================================
# AUTH HELPERS
# ============================================================================
async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Simple auth extractor for hackathon."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    # In production, verify JWT here. For now, return None or parse if needed.
    return None

# ============================================================================
# ENDPOINTS
# ============================================================================

# --- 1. HISTORY ENDPOINT (Matches Frontend) ---
@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """
    Frontend expects this specific route to load chat history.
    """
    logger = get_supabase_logger()
    try:
        # Fetch turns from Supabase
        history = await logger.get_session_history(session_id)
        
        # Format for Frontend (User/AI pairs)
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
                "content": turn['assistant_response']
            })
            
        return {"history": formatted_history}
    except Exception as e:
        print(f"❌ History Error: {e}")
        return {"history": []}

# --- 2. CHAT ENDPOINT ---
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    auth_user: Optional[str] = Depends(get_current_user)
):
    print(f"📥 Received: {request.message} | Session: {request.session_id}")
    
    try:
        logger = get_supabase_logger()
        
        # 1. Fetch Context (History)
        # We assume the frontend passes the relevant history, but we can also fetch it
        # to ensure the LLM has the full context if 'history' is empty.
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
        
        # 3. Log to Supabase
        # We calculate turn number based on existing history length
        turn_number = (len(history_context) // 2) + 1
        
        await logger.log_conversation_turn(
            session_id=request.session_id,
            turn_number=turn_number,
            user_message=request.message,
            assistant_response=result_state["final_response"],
            state_snapshot=result_state,
            agent_logs=result_state.get("agent_log", [])
        )
        
        return ChatResponse(
            response=result_state["final_response"],
            agent_logs=result_state["agent_log"],
            action_plan=result_state.get("action_plan", {})
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. SESSION MANAGEMENT (Optional/Advanced) ---
@app.get("/api/sessions")
async def list_sessions():
    """Placeholder for session listing."""
    # Logic: Query 'sessions' table distinct by session_id
    # For now return empty or implement in supabase_logger if needed
    return {"sessions": []}

@app.get("/health")
async def health_check():
    logger = get_supabase_logger()
    is_connected = await logger.health_check()
    return {"status": "healthy" if is_connected else "degraded"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)