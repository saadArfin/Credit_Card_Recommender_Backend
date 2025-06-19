import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from app.embedding_utils import generate_text_embedding
from app.gemini_api import genai_client


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# def parse_amount(text):
#     import re

#     text = text.lower().replace(",", "")
#     match = re.search(r"(\d+)(?:\s*(thousand|lakh|lakhs|million|crore|cr))?", text)
#     if not match:
#         return 0
#     num = int(match.group(1))
#     mult = 1
#     if match.group(2):
#         if "thousand" in match.group(2):
#             mult = 1000
#         elif "lakh" in match.group(2):
#             mult = 100000
#         elif "million" in match.group(2):
#             mult = 1000000
#         elif "crore" in match.group(2) or "cr" in match.group(2):
#             mult = 10000000
#     return num * mult


def extract_user_preferences_and_update_session(session: dict):
    """
    Uses Gemini Flash to extract preferences from session['history'] and updates session['preferences'] in-place.
    """
    from app.gemini_api import genai_client
    from google.genai import types
    import json

    # Compose chat history as a string
    chat = "\n".join(
        [f"{m['sender']}: {m['text']}" for m in session.get("history", [])]
    )

    # Compose the extraction prompt

    extraction_prompt = f"""
    You are a data extractor.

    Given the following chat history between a user and a credit card assistant, extract the user's preferences in **valid JSON format** with these exact fields and types:

    ```json
    {{
    "age": int or null,
    "income": int or null,
    "income_period": "monthly" or "annual" or null,
    "spending": {{
        "fuel": int,
        "travel": int,
        "groceries": int,
        "dining": int,
        "online_shopping": int,
        "utilities": int
    }},
    "custom_spending": {{
        "<other_category_name>": int
    }},
    "reward_preferences": [string],
    "bank_preference": string or null,
    "special_features": [string],
    "annual_fee_preference": true or false or null,
    "credit_score": string or null,
    "existing_cards": [string]
    }}

    """

    # Call Gemini Flash
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=extraction_prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        prefs = json.loads(response.text)
    except Exception as e:
        print("LLM extraction error:", e)
        prefs = {
            "age": None,
            "income": None,
            "income_period": None,
            "spending": {},
            "custom_spending": {},
            "reward_preferences": [],
            "bank_preference": None,
            "special_features": [],
            "annual_fee_preference": None,
            "credit_score": None,
            "existing_cards": [],
        }
    session["preferences"] = prefs
    return prefs


def simulate_rewards(card, prefs):
    """
    Simulate annual rewards for a card and user preferences using Gemini LLM (Flash).
    Falls back to regex-based method if LLM fails.
    """
    import re
    from app.gemini_api import genai_client
    from google.genai import types
    import json

    # Prepare prompt for Gemini
    prompt = f"""
    You are a financial assistant. Given the following credit card details and user spending preferences, estimate the total annual rewards the user could earn with this card. 
    
    Card details (JSON):
    {json.dumps(card, ensure_ascii=False, indent=2)}
    
    User spending preferences (JSON):
    {json.dumps(prefs.get('spending', {}), ensure_ascii=False, indent=2)}
    
    Please:
    - Calculate the total estimated annual rewards (in INR) for this user, based on the reward structure and spending.
    - Show a breakdown by category if possible.
    - If the reward structure is unclear, say so.
    - Respond in valid JSON with fields: {{"total_rewards_inr": int, "details": [string]}}.
    """
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        result = json.loads(response.text)
        total = result.get("total_rewards_inr", 0)
        details = result.get("details", [])
        if details:
            return f"You could earn approx. ₹{total:.0f}/year", details
    except Exception as e:
        print("LLM reward simulation error, falling back to regex:", e)

    #Fallback: regex-based method 
    total = 0
    details = []
    rr = card.get("reward_rate", "").lower()
    generic_cb_match = re.search(r"(\d+)% on (all|other|any) spends", rr)
    generic_pt_match = re.search(r"(\d+) points per [₹rs\\. ]*(\d+)", rr)
    for cat, spend in prefs.get("spending", {}).items():
        if spend == 0:
            continue
        cb_match = re.search(r"(\d+)%.*" + cat, rr)
        if cb_match:
            rate = float(cb_match.group(1)) / 100
            annual = spend * 12
            reward = annual * rate
            total += reward
            details.append(f"{rate*100:.0f}% cashback on {cat}: ₹{reward:.0f}/year")
            continue
        pt_match = re.search(r"(\d+) points per [₹rs\\. ]*(\d+).*(" + cat + ")", rr)
        if pt_match:
            pts = float(pt_match.group(1))
            per = float(pt_match.group(2))
            annual = spend * 12
            reward_points = (annual / per) * pts
            point_value = 0.25
            reward_inr = reward_points * point_value
            total += reward_inr
            details.append(
                f"{pts:.0f} points per ₹{per:.0f} on {cat}: {reward_points:.0f} points/year (~₹{reward_inr:.0f}/year)"
            )
            continue
        if generic_cb_match:
            rate = float(generic_cb_match.group(1)) / 100
            annual = spend * 12
            reward = annual * rate
            total += reward
            details.append(
                f"{rate*100:.0f}% cashback on {cat}: ₹{reward:.0f}/year (generic)"
            )
            continue
        if generic_pt_match:
            pts = float(generic_pt_match.group(1))
            per = float(generic_pt_match.group(2))
            annual = spend * 12
            reward_points = (annual / per) * pts
            point_value = 0.25
            reward_inr = reward_points * point_value
            total += reward_inr
            details.append(
                f"{pts:.0f} points per ₹{per:.0f} on {cat}: {reward_points:.0f} points/year (~₹{reward_inr:.0f}/year, generic)"
            )
    if details:
        return f"You could earn approx. ₹{total:.0f}/year", details
    return "Reward simulation not available", []


def llm_generate_recommendation_reason(card, prefs):
    """
    Use Gemini LLM to generate a natural language explanation for why this card is recommended.
    """

    user_summary = []
    if prefs.get("income"):
        user_summary.append(f"Income: {prefs['income']}")
    if prefs.get("age"):
        user_summary.append(f"Age: {prefs['age']}")
    if prefs.get("spending"):
        user_summary.append(
            "Spending: "
            + ", ".join(f"{k}: ₹{v}/mo" for k, v in prefs["spending"].items() if v)
        )
    if prefs.get("reward_preferences"):
        user_summary.append(
            "Preferred benefits: " + ", ".join(prefs["reward_preferences"])
        )
    if prefs.get("special_features"):
        user_summary.append("Special perks: " + ", ".join(prefs["special_features"]))
    if prefs.get("bank_preference"):
        user_summary.append(f"Preferred issuer: {prefs['bank_preference']}")
    if prefs.get("annual_fee_preference"):
        user_summary.append("Prefers low/waived fee")

    user_summary = "; ".join(user_summary)
    card_summary = f"Card: {card.get('name', '')}\nIssuer: {card.get('issuer', '')}\nAnnual Fee: {card.get('annual_fee', '')}\nReward Type: {card.get('reward_type', '')}\nReward Rate: {card.get('reward_rate', '')}\nSpecial Perks: {card.get('special_perks', '')}"
    prompt = (
        "Given the following user profile and credit card details, explain in 1-2 sentences why this card is a good fit for the user. Convince them why its a good fit for them or something llike that!"
        "Be specific and reference both the user's preferences and the card's features.\n"
        f"User profile: {user_summary}\nCard details: {card_summary}"
    )
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        return response.text.strip()
    except Exception as e:
        return "Explanation not available."


def generate_text_embedding_from_preferences(preferences: dict):
    """
    Generate a summary string from structured preferences for embedding.
    This ensures the embedding is based on key-value pairs, not just raw user text.
    """
    summary_parts = []
    if preferences.get("age"):
        summary_parts.append(f"Age: {preferences['age']}")
    if preferences.get("income"):
        summary_parts.append(
            f"Income: {preferences['income']} ({preferences.get('income_period', '')})"
        )
    if preferences.get("spending"):
        summary_parts.append(
            "Spending: "
            + ", ".join(
                f"{k}: ₹{v}/mo" for k, v in preferences["spending"].items() if v
            )
        )
    if preferences.get("custom_spending"):
        summary_parts.append(
            "Custom Spending: "
            + ", ".join(
                f"{k}: ₹{v}/mo" for k, v in preferences["custom_spending"].items() if v
            )
        )
    if preferences.get("reward_preferences"):
        summary_parts.append(
            "Reward Preferences: " + ", ".join(preferences["reward_preferences"])
        )
    if preferences.get("bank_preference"):
        summary_parts.append(f"Bank Preference: {preferences['bank_preference']}")
    if preferences.get("special_features"):
        summary_parts.append(
            "Special Features: " + ", ".join(preferences["special_features"])
        )
    if preferences.get("annual_fee_preference") is not None:
        summary_parts.append(
            f"Annual Fee Preference: {preferences['annual_fee_preference']}"
        )
    if preferences.get("credit_score"):
        summary_parts.append(f"Credit Score: {preferences['credit_score']}")
    if preferences.get("existing_cards"):
        summary_parts.append(
            "Existing Cards: " + ", ".join(preferences["existing_cards"])
        )
    summary_text = "; ".join(summary_parts)
    return generate_text_embedding(summary_text)


def get_top_credit_card_recommendations_from_session(
    session_or_history, pinecone_index, top_k: int = 3
) -> list[dict]:
    # Accept either a session dict or a history list for backward compatibility
    if isinstance(session_or_history, dict):
        prefs = session_or_history.get("preferences")
        history = session_or_history.get("history", [])
    else:
        prefs = None
        history = session_or_history
    if not prefs or not prefs.get("age"):
        from app.utils import extract_user_preferences_and_update_session

        # If only history is passed, wrap in a dict for compatibility
        session = {"history": history}
        prefs = extract_user_preferences_and_update_session(session)

    # Use preferences-based summary for embedding
    embedding = generate_text_embedding_from_preferences(prefs)
    cards = []
    result = pinecone_index.query(vector=embedding, top_k=top_k, include_metadata=True)
    cards = [match["metadata"] for match in result["matches"]]
    for card in cards:
        # sim, details = simulate_rewards(card, prefs)
        # card["reward_simulation"] = sim
        # card["reward_details"] = details
        card["llm_reason"] = llm_generate_recommendation_reason(card, prefs)
    return cards
