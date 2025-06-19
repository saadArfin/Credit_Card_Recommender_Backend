from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.gemini_api import chat_with_gemini, sessions, save_sessions
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from app.utils import (
    get_top_credit_card_recommendations_from_session,
    extract_user_preferences_and_update_session,
)

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("credit-cards")


router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    user_input: str


class ChatResponse(BaseModel):
    reply: str
    history: list[dict]


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.session_id or not req.user_input:
        raise HTTPException(
            status_code=400, detail="session_id and user_input required"
        )
    bot_reply = await chat_with_gemini(req.session_id, req.user_input)
    print("DEBUG: bot_reply:", bot_reply)
    return {"reply": bot_reply, "history": sessions[req.session_id]["history"]}


class RecommendResponse(BaseModel):
    recommendations: list


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(session_id: str, top_k: int = 3):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    print(
        "DEBUG: Session history before extracting preferences:", session.get("history")
    )
    extract_user_preferences_and_update_session(session)
    save_sessions()
    print("DEBUG: Preferences after extraction:", session.get("preferences"))

    recommendations = get_top_credit_card_recommendations_from_session(
        session, index, top_k=top_k
    )
    minimal_recommendations = [
        {
            "name": card.get("name", ""),
            "image_url": card.get("image_url", ""),
            "apply_link": card.get("apply_link", ""),
            "reward_simulation": card.get("reward_simulation", ""),
            "reward_details": card.get("reward_details", []),
            "llm_reason": card.get("llm_reason", ""),
        }
        for card in recommendations
    ]
    print("DEBUG: minimal_recommendations:", minimal_recommendations)
    return {"recommendations": minimal_recommendations}
