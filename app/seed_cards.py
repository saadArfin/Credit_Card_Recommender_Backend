import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from app.embedding_utils import generate_embedding
from pinecone import Pinecone

load_dotenv()

# Initialize Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("credit-cards")

# Initialize Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Convert to Embeddings and Prepare Vectors
vectors = []

with open("data/cards.json", "r", encoding="utf-8") as f:
    credit_cards = json.load(f)

for card in credit_cards:
    embedding = generate_embedding(card)
    # Extract float values from ContentEmbedding object's.values attribute
    embedding_floats = embedding[0].values
    vectors.append(
        {
            "id": card["name"].replace(" ", "_").lower(),
            "values": embedding_floats,
            "metadata": card,
        }
    )


# Insert into Pinecone 
# index.upsert(vectors=vectors)
# print(f"✅ Inserted {len(vectors)} credit cards into Pinecone.")
