# ============================================
# MANTHAN AI — Operational Chat Controller
# File: ai/chat.py
# ============================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.router import ask_ai  
from rag.retriever import retrieve_code_context  # ← Integrating vector fetching logic

router = APIRouter()

class ChatRequest(BaseModel):
    task: str       # Example: 'chat', 'fix', 'explain', 'enhance' 
    message: str    # The actual text input from the developer inside VS Code editor window [cite: 8]
    use_rag: bool = True  # Toggle parameter to control automatic codebase lookup flows

@router.post("/chat")
async def chat_with_ai(payload: ChatRequest):
    """
    Primary API gateway receiving prompts from user's VS Code UI.
    Extracts relevant context vectors from local store before routing to models.
    """
    try:
        context_string = ""
        
        # Automatically extract local code insights if RAG flag is up
        if payload.use_rag:
            print(f"[Chat Endpoint] Fetching structural codebase nodes context for query: '{payload.message}'")
            context_string = retrieve_code_context(query=payload.message, max_results=3)

        # Triggering dynamic router execution mappings
        ai_response_package = await ask_ai(
            task=payload.task,
            user_message=payload.message,
            context=context_string
        )
        
        return {
            "status": "success",
            "data": ai_response_package
        }
        
    except Exception as e:
        print(f"[Chat Endpoint] Execution sequence failure exception caught: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))