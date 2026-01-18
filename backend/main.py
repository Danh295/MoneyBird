<<<<<<< HEAD
from fastapi import FastAPI, HTTPException
=======
"""
main.py - The API Entrypoint with Supabase Session & Auth Management
"""
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Depends
>>>>>>> feature/auth
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from schemas import ChatRequest, ChatResponse
from workflow import run_mindmoney_workflow
<<<<<<< HEAD
from supabase_logger import get_supabase_logger
=======
from supabase_logger import get_supabase_service
>>>>>>> feature/auth
import uvicorn
import uuid

app = FastAPI(title="MindMoney API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< HEAD
# --- 1. NEW: Get All Sessions ---
@app.get("/api/sessions")
async def get_sessions():
    """Get all chat sessions with preview."""
    logger = get_supabase_logger()
    try:
        sessions = await logger.get_all_sessions(limit=50)
        return {"sessions": sessions}
    except Exception as e:
        print(f"❌ Sessions Error: {e}")
        return {"sessions": []}

# --- 2. NEW: History Endpoint (Restores Chat) ---
@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    logger = get_supabase_logger()
    try:
        # Fetch last 50 turns from Supabase
        history = await logger.get_session_history(session_id)
        
        # Format for Frontend
        formatted_history = []
        for turn in history:
            # Add User Message
            formatted_history.append({
                "id": f"{turn['id']}-user",
                "role": "user",
                "content": turn['user_message']
            })
            # Add AI Response
            formatted_history.append({
                "id": f"{turn['id']}-ai",
                "role": "assistant",
                "content": turn['assistant_response']
            })
            
        return {"history": formatted_history}
    except Exception as e:
        print(f"❌ History Error: {e}")
        return {"history": []}

# --- 3. UPDATED: Chat Endpoint (Saves to DB) ---
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    print(f"📥 Received: {request.message} (Session: {request.session_id})")
    
    try:
        # 1. Run the AI Workflow
=======

# ============================================================================
# AUTH HELPERS
# ============================================================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Extract user_id from Authorization header.
    Expected format: "Bearer <supabase_access_token>"
    
    In production, you'd verify the JWT token with Supabase.
    For hackathon, we'll trust the user_id passed in the request.
    """
    if not authorization:
        return None
    
    try:
        # For production: Verify JWT with Supabase
        # from supabase import create_client
        # client = create_client(url, key)
        # user = client.auth.get_user(token)
        # return user.id
        
        # For hackathon: Just extract from header if present
        if authorization.startswith("Bearer "):
            # In real implementation, decode JWT and get user_id
            # For now, return None (anonymous user)
            return None
        return None
    except Exception:
        return None


# ============================================================================
# REQUEST MODELS
# ============================================================================

class AuthChatRequest(BaseModel):
    message: str
    history: list = []
    session_id: str = "demo-session"
    user_id: Optional[str] = None  # Optional user ID for authenticated requests


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: AuthChatRequest,
    auth_user: Optional[str] = Depends(get_current_user)
):
    """Main chat endpoint with optional user authentication."""
    # Use user_id from request body or from auth header
    user_id = request.user_id or auth_user
    
    print(f"📥 Received: {request.message} | Session: {request.session_id} | User: {user_id or 'anonymous'}")
    
    try:
        supabase = get_supabase_service()
        
        # Load existing session history from Supabase
        conversation_history = request.history
        turn_number = 1
        
        session_context = await supabase.load_session_context(
            request.session_id, 
            user_id=user_id
        )
        
        if session_context["turn_count"] > 0:
            print(f"📚 Loading existing session with {session_context['turn_count']} turns")
            conversation_history = session_context["conversation_history"]
            turn_number = session_context["turn_count"] + 1
        
        # Run the LangGraph workflow
>>>>>>> feature/auth
        result_state = await run_mindmoney_workflow(
            user_input=request.message,
            history=conversation_history
        )
        
        # Log to Supabase (async)
        asyncio.create_task(
            supabase.log_conversation_turn(
                session_id=request.session_id,
                turn_number=turn_number,
                user_message=request.message,
                assistant_response=result_state["final_response"],
                state_snapshot=result_state,
                agent_logs=result_state.get("agent_log", []),
                user_id=user_id
            )
        )
        
        # 2. LOG TO SUPABASE
        logger = get_supabase_logger()
        
        # Update session metadata
        await logger.create_or_update_session(request.session_id, request.message)
        
        # Log conversation turn
        await logger.log_conversation_turn(
            session_id=request.session_id,
            turn_number=len(request.history) + 1, 
            user_message=request.message,
            assistant_response=result_state["final_response"],
            state_snapshot=result_state,
            agent_logs=result_state["agent_log"]
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
async def list_sessions(
    user_id: Optional[str] = None,
    auth_user: Optional[str] = Depends(get_current_user)
):
    """List all sessions for a user."""
    effective_user_id = user_id or auth_user
    
    try:
        supabase = get_supabase_service()
        sessions = await supabase.get_all_sessions(user_id=effective_user_id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"❌ Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session(
    session_id: str,
    user_id: Optional[str] = None,
    auth_user: Optional[str] = Depends(get_current_user)
):
    """Load a specific session's full context."""
    effective_user_id = user_id or auth_user
    
    try:
        supabase = get_supabase_service()
        
        exists = await supabase.session_exists(session_id, user_id=effective_user_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Session not found")
        
        context = await supabase.load_session_context(session_id, user_id=effective_user_id)
        turns = await supabase.get_session_history(session_id, user_id=effective_user_id)
        
        return {
            "session_id": session_id,
            "conversation_history": context["conversation_history"],
            "turn_count": context["turn_count"],
            "last_intake_profile": context["last_intake_profile"],
            "turns": turns
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error loading session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(
    session_id: str, 
    limit: int = 50,
    user_id: Optional[str] = None,
    auth_user: Optional[str] = Depends(get_current_user)
):
    """Get conversation history for a session."""
    effective_user_id = user_id or auth_user
    
    try:
        supabase = get_supabase_service()
        history = await supabase.load_session_history(
            session_id, 
            user_id=effective_user_id,
            limit=limit
        )
        return {
            "session_id": session_id,
            "history": history,
            "count": len(history) // 2
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/logs")
async def get_session_logs(
    session_id: str,
    user_id: Optional[str] = None,
    auth_user: Optional[str] = Depends(get_current_user)
):
    """Get agent logs for a session."""
    effective_user_id = user_id or auth_user
    
    try:
        supabase = get_supabase_service()
        logs = await supabase.get_agent_logs(session_id, user_id=effective_user_id)
        return {
            "session_id": session_id,
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/profile")
async def get_user_profile(
    user_id: str,
    auth_user: Optional[str] = Depends(get_current_user)
):
    """Get user profile."""
    effective_user_id = user_id or auth_user
    
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    try:
        supabase = get_supabase_service()
        profile = await supabase.get_user_profile(effective_user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return profile
    except HTTPException:
        raise
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
        "auth": "Supabase Auth supported",
        "endpoints": {
            "chat": "POST /api/chat",
            "list_sessions": "GET /api/sessions",
            "get_session": "GET /api/sessions/{session_id}",
            "session_history": "GET /api/sessions/{session_id}/history",
            "session_logs": "GET /api/sessions/{session_id}/logs",
            "user_profile": "GET /api/user/profile",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)