# from fastapi import FastAPI
# from app.routes import router

# app = FastAPI(
#     title="Gemini Assistant",
#     description="FastAPI app using Gemini 2.5 Flash",
#     version="1.0.0",
# )

# app.include_router(router)


# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.routes import router

# app = FastAPI(title="Credit Card Recommender Bot")

# # CORS for frontend
# auth_origins = ["*"]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=auth_origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(router)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(title="Credit Card Recommender Bot")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

