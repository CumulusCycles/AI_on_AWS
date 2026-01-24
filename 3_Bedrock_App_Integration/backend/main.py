"""
FastAPI application entry point for the Bedrock App Integration API.

Provides: /health, /config, /chat (damage assessment), /conversations (CRUD),
/admin/* (analytics, conversations, models, system). CORS is enabled for
chat-frontend (3000) and admin-frontend (3001); origins come from CORS_ORIGINS.

Run: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from routers import config, chat, conversations, admin

app = FastAPI(
    title="AWS Bedrock App Integration API",
    docs_url="/docs",
)

# CORS: allow chat (3000) and admin (3001) frontends; configurable via CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route groups: config (health, /config), chat (/chat), conversations (CRUD), admin (/admin/*)
app.include_router(config.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(admin.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
