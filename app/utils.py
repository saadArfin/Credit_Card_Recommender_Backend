import os
from dotenv import load_dotenv
from google.generativeai import embed_content
from google import genai
from google.genai import types
from app.embedding_utils import generate_embedding, generate_text_embedding
from app.gemini_api import genai_client
import json

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# def extract_user_preferences(session_history):
#     prefs = {
#         "age": None,
#         "income": None,
#         "spend": {},
#         "preferred_benefits": [],
#         "issuer": None,
#         "special_perks": [],
#         "low_fee": False,
#     }
#     last_q = ""
#     for m in session_history:
#         if m["sender"] == "bot":
#             last_q = m["text"].lower()
#         elif m["sender"] == "user":
#             ans = m["text"].lower()
#             if "age" in last_q:
#                 try:
#                     prefs["age"] = int([int(s) for s in ans.split() if s.isdigit()][0])
#                 except:
#                     pass
#             elif "income" in last_q:
#                 prefs["income"] = ans
#             elif "fuel" in last_q:
#                 prefs["spend"]["fuel"] = (
#                     int("".join([c for c in ans if c.isdigit()]))
#                     if any(x.isdigit() for x in ans)
#                     else 0
#                 )
#             elif "travel" in last_q:
#                 prefs["spend"]["travel"] = (
#                     int("".join([c for c in ans if c.isdigit()]))
#                     if any(x.isdigit() for x in ans)
#                     else 0
#                 )
#             elif "grocer" in last_q:
#                 prefs["spend"]["groceries"] = (
#                     int("".join([c for c in ans if c.isdigit()]))
#                     if any(x.isdigit() for x in ans)
#                     else 0
#                 )
#             elif "dining" in last_q:
#                 prefs["spend"]["dining"] = (
#                     int("".join([c for c in ans if c.isdigit()]))
#                     if any(x.isdigit() for x in ans)
#                     else 0
#                 )
#             elif "online shopping" in last_q:
#                 prefs["spend"]["online"] = (
#                     int("".join([c for c in ans if c.isdigit()]))
#                     if any(x.isdigit() for x in ans)
#                     else 0
#                 )
#             elif "utilit" in last_q:
#                 prefs["spend"]["utilities"] = (
#                     int("".join([c for c in ans if c.isdigit()]))
#                     if any(x.isdigit() for x in ans)
#                     else 0
#                 )
#             # Custom spending category support
#             elif "spending" in last_q or "spend" in last_q:
#                 # Try to extract category from the question
#                 import re

#                 match = re.search(r"spending on ([a-zA-Z ]+)[?]", last_q)
#                 if match:
#                     cat = match.group(1).strip().replace(" ", "_")
#                     prefs["spend"][cat] = (
#                         int("".join([c for c in ans if c.isdigit()]))
#                         if any(x.isdigit() for x in ans)
#                         else 0
#                     )
#             elif "benefit" in last_q or "reward" in last_q:
#                 prefs["preferred_benefits"] = [
#                     b.strip() for b in ans.replace("and", ",").split(",")
#                 ]
#             elif "issuer" in last_q or "bank" in last_q:
#                 prefs["issuer"] = ans if ans != "no" else None
#             elif "perk" in last_q:
#                 prefs["special_perks"] = [
#                     b.strip() for b in ans.replace("and", ",").split(",")
#                 ]
#             elif "fee" in last_q:
#                 prefs["low_fee"] = "yes" in ans or "yews" in ans or "low" in ans
#     return prefs


def parse_amount(text):
    import re

    text = text.lower().replace(",", "")
    match = re.search(r"(\d+)(?:\s*(thousand|lakh|lakhs|million|crore|cr))?", text)
    if not match:
        return 0
    num = int(match.group(1))
    mult = 1
    if match.group(2):
        if "thousand" in match.group(2):
            mult = 1000
        elif "lakh" in match.group(2):
            mult = 100000
        elif "million" in match.group(2):
            mult = 1000000
        elif "crore" in match.group(2) or "cr" in match.group(2):
            mult = 10000000
    return num * mult


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
Given the following chat history between a user and a credit card assistant, extract the user's preferences as a JSON object with these fields:
- age (int or null)
- income (int or null)
- income_period (\"monthly\", \"annual\", or null)
- spending (dict of category: int)
- custom_spending (dict of category: int)
- reward_preferences (list of strings)
- bank_preference (string or null)
- special_features (list of strings)
- annual_fee_preference (bool or null)
- credit_score (string or null)
- existing_cards (list of strings)

Chat history:
{chat}

Respond ONLY with the JSON object.
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


def get_recommendation_reasons(card, prefs):
    reasons = []
    for benefit in prefs["reward_preferences"]:
        if (
            benefit
            and benefit.lower() in card.get("reward_type", "").lower()
            or benefit.lower() in card.get("special_perks", "").lower()
        ):
            reasons.append(f"Matches your preference: {benefit}")
    for cat in prefs["spending"]:
        if cat in card.get("reward_rate", "").lower():
            reasons.append(f"High rewards on {cat}")
    if (
        prefs["bank_preference"]
        and prefs["bank_preference"] in card.get("issuer", "").lower()
    ):
        reasons.append(f"Preferred issuer: {prefs['bank_preference']}")
    if prefs["annual_fee_preference"]:
        try:
            fee = int("".join([c for c in card.get("annual_fee", "") if c.isdigit()]))
            if fee <= 1000:
                reasons.append("Low annual fee")
        except:
            pass
    for perk in prefs["special_features"]:
        if perk and perk.lower() in card.get("special_perks", "").lower():
            reasons.append(f"Includes perk: {perk}")
    return reasons or ["General match to your preferences"]


def simulate_rewards(card, prefs):
    # Improved: fallback to generic rates if category-specific not found
    total = 0
    details = []
    rr = card.get("reward_rate", "").lower()
    import re

    # Fallback: look for generic rates
    generic_cb_match = re.search(r"(\d+)% on (all|other|any) spends", rr)
    generic_pt_match = re.search(r"(\d+) points per [₹rs\. ]*(\d+)", rr)
    for cat, spend in prefs["spending"].items():
        if spend == 0:
            continue
        # Try category-specific cashback
        cb_match = re.search(r"(\d+)%.*" + cat, rr)
        if cb_match:
            rate = float(cb_match.group(1)) / 100
            annual = spend * 12
            reward = annual * rate
            total += reward
            details.append(f"{rate*100:.0f}% cashback on {cat}: ₹{reward:.0f}/year")
            continue
        # Try category-specific points
        pt_match = re.search(r"(\d+) points per [₹rs\. ]*(\d+).*(" + cat + ")", rr)
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
        # Fallback: generic cashback
        if generic_cb_match:
            rate = float(generic_cb_match.group(1)) / 100
            annual = spend * 12
            reward = annual * rate
            total += reward
            details.append(
                f"{rate*100:.0f}% cashback on {cat}: ₹{reward:.0f}/year (generic)"
            )
            continue
        # Fallback: generic points
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
    # Compose a prompt for the LLM
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
        "Given the following user profile and credit card details, explain in 1-2 sentences why this card is a good fit for the user. Always tell them its a good fit for them or something llike that!"
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
        print("LLM reason generation error:", e)
        return "AI explanation not available."


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
        card["reasons"] = get_recommendation_reasons(card, prefs)
        sim, details = simulate_rewards(card, prefs)
        card["reward_simulation"] = sim
        card["reward_details"] = details
        # Add LLM-powered explanation
        card["llm_reason"] = llm_generate_recommendation_reason(card, prefs)
    return cards
