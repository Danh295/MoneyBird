"""
main.py - The API Entrypoint
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas import ChatRequest, ChatResponse
from workflow import run_mindmoney_workflow
import uvicorn

app = FastAPI(title="MindMoney API")

# Allow React to talk to Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for hackathon (safer/easier)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    print(f"📥 Received: {request.message}")
    
    try:
        # Run the LangGraph Brain (4-agent workflow)
        result_state = await run_mindmoney_workflow(
            user_input=request.message,
            history=request.history
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