# Credit Card Agent (FastAPI Backend)

A robust, explainable, LLM-powered credit card recommendation backend for Indian users. Guides users through a Q&A journey, extracts and stores structured preferences, and uses these for vector search, reward simulation, and explanations.

---

## Features
- Conversational, LLM-powered Q&A to extract user preferences
- Gemini (Google Generative AI) for chat, embeddings, and explanations
- Pinecone for vector search and card similarity
- Reward simulation and explainable recommendations (LLM + fallback logic)
- Session management (in-memory and file-based)
- Cloud-ready: deployable to Render.com or any cloud platform
- Easy integration with modern frontend (Next.js, etc.)

---

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

---

## Setup Instructions

1. **Clone the repo**
   ```sh
   git clone <your-repo-url>
   cd CreditCardAgent
   ```
2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Set environment variables**
   - Create a `.env` file with:
     ```
     GEMINI_API_KEY=your_gemini_api_key
     PINECONE_API_KEY=your_pinecone_api_key
     ```
4. **Run the backend**
   ```sh
   uvicorn app.main:app --reload
   ```
5. **API Endpoints**
   - `POST /chat`: Conversational chat endpoint.
   - `POST /recommend`: Get top card recommendations for a session.

---

## Agent Flow & Prompt Design

- **Session-based Q&A**: Each user session stores chat history and extracted preferences.
- **LLM Extraction**: Gemini Flash extracts structured preferences from chat.
- **Vector Search**: User preferences are embedded and matched against card embeddings in Pinecone.
- **LLM Reasoning**: Each card recommendation includes an custom LLM-generated explanation and reward simulation.

---

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

---

## API Endpoints
- `POST /chat` — Conversational chat endpoint
- `POST /recommend` — Get credit card recommendations

---

## License
MIT
