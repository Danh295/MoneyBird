from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import ChatRequest, ChatResponse
from workflow import run_mindmoney_workflow
from supabase_logger import get_supabase_logger
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
        result_state = await run_mindmoney_workflow(
            user_input=request.message,
            history=request.history
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)