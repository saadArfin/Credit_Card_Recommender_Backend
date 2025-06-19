import os
from dotenv import load_dotenv
from google import genai
# import google.generativeai as genai  

from google.genai import types
from app.system_prompt import SYSTEM_PROMPT
from app.embedding_utils import generate_embedding
import json
from pathlib import Path

SESSIONS_FILE = Path("sessions.json")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

genai_client = genai.Client(api_key=api_key)

# In-memory store for sessions: { session_id: { history: [], preferences: {} } }
sessions: dict = {}

if SESSIONS_FILE.exists():
    try:
        with open(SESSIONS_FILE, "r") as f:
            sessions = json.load(f)
    except Exception as e:
        print("Failed to load sessions.json:", e)


def save_sessions():
    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        print("Failed to save sessions.json:", e)


# Ask Gemini using the documented way
def ask_gemini(prompt: str) -> str:
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        return response.text
    except Exception as e:
        print("Gemini Error:", e)
        return "⚠️ Error from Gemini."


async def chat_with_gemini(session_id: str, user_input: str) -> str:
    session = sessions.setdefault(session_id, {"history": [], "preferences": {}})
    # Ensure the initial bot message is present for every new session
    INITIAL_BOT_MESSAGE = "Hello! 👋 I can help you find the best credit card for your needs. To get started, may I know your age?"
    if not session["history"]:
        session["history"].append({"sender": "bot", "text": INITIAL_BOT_MESSAGE})

    session["history"].append({"sender": "user", "text": user_input})

    prompt = "\n".join([f"{m['sender']}: {m['text']}" for m in session["history"]])
    # System prompt for Gemini
    full_prompt = f"{SYSTEM_PROMPT}\n{prompt}"

    bot_reply = ask_gemini(full_prompt)
    session["history"].append({"sender": "bot", "text": bot_reply})



    save_sessions()  # ← persist data after each reply

    return bot_reply
