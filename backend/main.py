"""
MindMoney Backend - FastAPI Application

A multi-agent financial therapy chatbot that combines:
- Gemini (Intake Specialist): Emotion and identity analysis
- Anthropic Claude (Financial Planner): Financial fact extraction and planning
- OpenAI (Synthesizer): Response generation with conditional routing
"""

import json
import asyncio
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from config import get_settings
from schemas import (
    ChatRequest, 
    ChatResponse, 
    StateResponse, 
    HealthResponse,
    SSEEventType
)
from workflow import run_mindmoney_workflow
from state_manager import RedisStateManager, get_state_manager
from supabase_logger import SupabaseLogger, get_supabase_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 MindMoney Backend starting up...")
    state_manager = get_state_manager()
    yield
    print("👋 MindMoney Backend shutting down...")
    await state_manager.close()


# Create FastAPI app
app = FastAPI(
    title="MindMoney API",
    description="Multi-agent financial therapy chatbot backend",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
settings = get_settings()
origins = settings.cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "MindMoney API",
        "version": "1.0.0",
        "description": "Multi-agent financial therapy chatbot",
        "docs": "/docs",
        "agents": [
            {"name": "Intake Specialist", "model": "Gemini", "role": "Emotion & Identity Analysis"},
            {"name": "Financial Planner", "model": "Anthropic Claude", "role": "Financial Extraction & Planning"},
            {"name": "Synthesizer", "model": "OpenAI GPT", "role": "Response Generation & Routing"}
        ]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    state_manager = get_state_manager()
    logger = get_supabase_logger()
    
    redis_ok = await state_manager.health_check()
    supabase_ok = await logger.health_check()
    
    status = "healthy" if (redis_ok and supabase_ok) else "degraded"
    
    return HealthResponse(
        status=status,
        redis_connected=redis_ok,
        supabase_connected=supabase_ok
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    state_manager: RedisStateManager = Depends(get_state_manager),
    logger: SupabaseLogger = Depends(get_supabase_logger)
):
    """
    Main chat endpoint. Processes user message through the 3-agent workflow.
    """
    try:
        existing_state = await state_manager.get_state(request.session_id)
        conversation_history = await state_manager.get_conversation_history(request.session_id)
        
        result = await run_mindmoney_workflow(
            session_id=request.session_id,
            user_input=request.message,
            conversation_history=conversation_history,
            existing_state=existing_state
        )
        
        await state_manager.save_state(request.session_id, dict(result))
        await state_manager.append_to_history(
            request.session_id,
            request.message,
            result.get("final_response", "")
        )
        
        # Log to Supabase (fire and forget)
        asyncio.create_task(
            logger.log_conversation_turn(
                session_id=request.session_id,
                turn_number=result.get("turn_number", 1),
                user_message=request.message,
                assistant_response=result.get("final_response", ""),
                state_snapshot=dict(result),
                agent_logs=result.get("agent_log", [])
            )
        )
        
        return ChatResponse(
            session_id=request.session_id,
            response=result.get("final_response", ""),
            state=dict(result) if request.include_state else None,
            agent_log=result.get("agent_log", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow error: {str(e)}")


@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    state_manager: RedisStateManager = Depends(get_state_manager),
    logger: SupabaseLogger = Depends(get_supabase_logger)
):
    """
    Streaming chat endpoint using Server-Sent Events.
    Streams state updates and agent logs in real-time.
    """
    
    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            existing_state = await state_manager.get_state(request.session_id)
            conversation_history = await state_manager.get_conversation_history(request.session_id)
            
            yield {
                "event": SSEEventType.STATE_UPDATE.value,
                "data": json.dumps({
                    "status": "started",
                    "session_id": request.session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
            
            result = await run_mindmoney_workflow(
                session_id=request.session_id,
                user_input=request.message,
                conversation_history=conversation_history,
                existing_state=existing_state
            )
            
            # Stream agent logs
            for log_entry in result.get("agent_log", []):
                yield {
                    "event": SSEEventType.AGENT_LOG.value,
                    "data": json.dumps(log_entry)
                }
                await asyncio.sleep(0.1)
            
            # Stream state update
            yield {
                "event": SSEEventType.STATE_UPDATE.value,
                "data": json.dumps({
                    "intake_profile": result.get("intake_profile", {}),
                    "financial_profile": result.get("financial_profile", {}),
                    "strategy_decision": result.get("strategy_decision", {}),
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
            
            # Stream final response
            yield {
                "event": SSEEventType.FINAL_RESPONSE.value,
                "data": json.dumps({
                    "response": result.get("final_response", ""),
                    "session_id": request.session_id,
                    "turn_number": result.get("turn_number", 1)
                })
            }
            
            await state_manager.save_state(request.session_id, dict(result))
            await state_manager.append_to_history(
                request.session_id,
                request.message,
                result.get("final_response", "")
            )
            
            asyncio.create_task(
                logger.log_conversation_turn(
                    session_id=request.session_id,
                    turn_number=result.get("turn_number", 1),
                    user_message=request.message,
                    assistant_response=result.get("final_response", ""),
                    state_snapshot=dict(result),
                    agent_logs=result.get("agent_log", [])
                )
            )
            
        except Exception as e:
            yield {
                "event": SSEEventType.ERROR.value,
                "data": json.dumps({
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
    
    return EventSourceResponse(event_generator())


@app.get("/api/chat/state/{session_id}", response_model=StateResponse)
async def get_state(
    session_id: str,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Get current state for a session."""
    state = await state_manager.get_state(session_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return StateResponse(
        session_id=session_id,
        state=state,
        last_updated=datetime.fromisoformat(state.get("_last_updated", datetime.utcnow().isoformat()))
    )


@app.get("/api/chat/history/{session_id}")
async def get_history(
    session_id: str,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Get conversation history for a session."""
    history = await state_manager.get_conversation_history(session_id)
    
    return {
        "session_id": session_id,
        "turns": history,
        "count": len(history)
    }


@app.delete("/api/chat/session/{session_id}")
async def delete_session(
    session_id: str,
    state_manager: RedisStateManager = Depends(get_state_manager)
):
    """Delete a session and all its data."""
    await state_manager.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}


@app.get("/api/chat/logs/{session_id}")
async def get_logs(
    session_id: str,
    logger: SupabaseLogger = Depends(get_supabase_logger)
):
    """Get persisted agent logs from Supabase."""
    logs = await logger.get_agent_logs(session_id)
    
    return {
        "session_id": session_id,
        "logs": logs,
        "count": len(logs)
    }


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )