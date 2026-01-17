"""
main.py - The API Entrypoint with Supabase Session Management
"""
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import ChatRequest, ChatResponse
from workflow import run_mindmoney_workflow
from supabase_logger import get_supabase_service
import uvicorn

app = FastAPI(title="MindMoney API")

# Allow React to talk to Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    print(f"📥 Received: {request.message} | Session: {request.session_id}")
    
    try:
        supabase = get_supabase_service()
        
        # =====================================================================
        # STEP 1: Load existing session history from Supabase (if session exists)
        # =====================================================================
        conversation_history = request.history  # Start with what frontend sent
        turn_number = 1
        
        # Check if this session has previous turns in Supabase
        session_context = await supabase.load_session_context(request.session_id)
        
        if session_context["turn_count"] > 0:
            # Session exists - merge histories (Supabase takes precedence)
            print(f"📚 Loading existing session with {session_context['turn_count']} turns")
            conversation_history = session_context["conversation_history"]
            turn_number = session_context["turn_count"] + 1
        
        # =====================================================================
        # STEP 2: Run the LangGraph Brain (4-agent workflow)
        # =====================================================================
        result_state = await run_mindmoney_workflow(
            user_input=request.message,
            history=conversation_history
        )
        
        # =====================================================================
        # STEP 3: Log this turn to Supabase (async, don't block response)
        # =====================================================================
        asyncio.create_task(
            supabase.log_conversation_turn(
                session_id=request.session_id,
                turn_number=turn_number,
                user_message=request.message,
                assistant_response=result_state["final_response"],
                state_snapshot=result_state,
                agent_logs=result_state.get("agent_log", [])
            )
        )
        
        return ChatResponse(
            response=result_state["final_response"],
            agent_logs=result_state["agent_log"],
            action_plan=result_state.get("action_plan", {})
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def list_sessions(user_id: str = None):
    """List all available sessions (for session selector UI)."""
    try:
        supabase = get_supabase_service()
        sessions = await supabase.get_all_sessions(user_id=user_id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"❌ Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Load a specific session's full context.
    Use this when user clicks on a session to resume it.
    """
    try:
        supabase = get_supabase_service()
        
        # Check if session exists
        exists = await supabase.session_exists(session_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Load full context
        context = await supabase.load_session_context(session_id)
        
        # Also get the raw turns for display
        turns = await supabase.get_session_history(session_id)
        
        return {
            "session_id": session_id,
            "conversation_history": context["conversation_history"],
            "turn_count": context["turn_count"],
            "last_intake_profile": context["last_intake_profile"],
            "turns": turns  # Full turn data for UI display
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error loading session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 50):
    """Get conversation history for a session (for chat UI)."""
    try:
        supabase = get_supabase_service()
        history = await supabase.load_session_history(session_id, limit=limit)
        return {
            "session_id": session_id,
            "history": history,
            "count": len(history) // 2  # Number of turns (user + assistant = 1 turn)
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/logs")
async def get_session_logs(session_id: str):
    """Get agent logs for a session (for debug panel)."""
    try:
        supabase = get_supabase_service()
        logs = await supabase.get_agent_logs(session_id)
        return {
            "session_id": session_id,
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        supabase = get_supabase_service()
        supabase_ok = await supabase.health_check()
        return {
            "status": "healthy" if supabase_ok else "degraded",
            "supabase_connected": supabase_ok
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "MindMoney API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /api/chat",
            "list_sessions": "GET /api/sessions",
            "get_session": "GET /api/sessions/{session_id}",
            "session_history": "GET /api/sessions/{session_id}/history",
            "session_logs": "GET /api/sessions/{session_id}/logs",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)