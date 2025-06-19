# Credit Card Agent (FastAPI Backend)

A robust, explainable, LLM-powered credit card recommendation backend for Indian users. Guides users through a Q&A journey, extracts and stores structured preferences, and uses these for vector search, reward simulation, and LLM explanations.

## Features
- Conversational Q&A to extract user preferences
- Gemini LLM for chat, embeddings, and explanations
- Pinecone for vector search
- Reward simulation and explainable recommendations
- Session management (in-memory and file-based)
- Ready for integration with a modern frontend

## Project Structure
```
app/
  embedding_utils.py   # Embedding logic
  gemini_api.py        # Gemini API integration & session management
  main.py              # FastAPI app entrypoint
  routes.py            # API endpoints
  seed_cards.py        # Pinecone seeding
  system_prompt.py     # System prompt for LLM
  utils.py             # Preference extraction, simulation, etc.
data/
  cards.json           # Credit card data
sessions.json          # Session storage (ephemeral on Render)
requirements.txt       # Python dependencies
.env                   # API keys (do NOT commit)
```

## Quickstart (Local)
1. Clone the repo and install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Add your `.env` file with Gemini and Pinecone API keys.
3. Run the app:
   ```sh
   uvicorn app.main:app --reload
   ```
4. Access the API at `http://localhost:8000`.

## Deployment (Render.com)
1. Push your code to GitHub (do NOT commit `.env` or `sessions.json`).
2. Create a new Web Service on Render, connect your repo.
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
5. Add your environment variables in the Render dashboard.
6. Deploy and get your public URL.

**Note:**
- File-based session storage (`sessions.json`) is ephemeral on Render. For production, use a database.
- Do NOT commit your `.env` file or secrets.

## API Endpoints
- `POST /chat` — Conversational chat endpoint
- `POST /recommend` — Get credit card recommendations

## License
MIT
