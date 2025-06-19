from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_embedding(card: dict):
    # Convert the card to a flat text string for embedding
    card_text = f"""
    Name: {card['name']}
    Issuer: {card['issuer']}
    Joining Fee: {card['joining_fee']}
    Annual Fee: {card['annual_fee']}
    Reward Type: {card['reward_type']}
    Reward Rate: {card['reward_rate']}
    Eligibility: {card['eligibility']}
    Perks: {card['special_perks']}
    """
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=card_text,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
    )
    embedding = result.embeddings
    print("DEBUG: embedding type:", type(embedding))
    print("DEBUG: embedding value:", embedding)
    # Flatten if nested (e.g., [[...]] instead of [...])
    if (
        isinstance(embedding, list)
        and len(embedding) == 1
        and isinstance(embedding[0], list)
    ):
        embedding = embedding[0]
    print("DEBUG: final embedding type:", type(embedding))
    print("DEBUG: final embedding value:", embedding)
    return embedding


def generate_text_embedding(text: str):
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
    )
    embedding = result.embeddings
    # If embedding is a list of ContentEmbedding, get the .values from the first
    if isinstance(embedding, list) and hasattr(embedding[0], "values"):
        return embedding[0].values
    return embedding


# with open("data/cards.json", "r", encoding="utf-8") as f:
#     credit_cards = json.load(f)

# vector = generate_embedding(credit_cards[0])
# print(f"Generated embedding for {credit_cards[0]['name']}: {vector}")
