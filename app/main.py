"""FastAPI backend for the Vault Electronics chatbot."""
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import Database
from app.nlp import ChatEngine

# When packaged with PyInstaller the data/config live next to the exe.
BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(os.environ.get("VAULT_CONFIG", BASE_DIR / "config.json"))

with open(CONFIG_PATH, encoding="utf-8") as f:
    CONFIG = json.load(f)

(BASE_DIR / "logs").mkdir(exist_ok=True)
db = Database(BASE_DIR / CONFIG.get("database", "data/chatbot.db"))
engine = ChatEngine(BASE_DIR, CONFIG)

app = FastAPI(title="Vault Electronics Chatbot", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.get("allowed_origins", ["*"]),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
if (BASE_DIR / "widget").exists():
    app.mount("/widget", StaticFiles(directory=BASE_DIR / "widget", html=True), name="widget")


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, max_length=64)
    page_url: Optional[str] = Field(None, max_length=300)


class FeedbackIn(BaseModel):
    message_id: int
    rating: int = Field(..., description="1 = helpful, -1 = not helpful")
    comment: Optional[str] = Field(None, max_length=500)


@app.post("/chat")
def chat(body: ChatIn, request: Request):
    start = time.perf_counter()
    text = body.message.strip()
    if not text:
        raise HTTPException(422, "Message is empty")
    sid = db.ensure_session(body.session_id, request.headers.get("user-agent"), body.page_url)
    last_intent, pending = db.get_state(sid)
    result = engine.reply(text, last_intent, pending)
    ms = int((time.perf_counter() - start) * 1000)
    mid = db.log_message(sid, text, result, ms)
    db.set_state(sid, result["intent"], result.get("offer"))
    return {"session_id": sid, "message_id": mid, "response": result["response"], "intent": result["intent"],
            "confidence": result["confidence"], "source": result["source"]}


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": engine.model is not None, "version": app.version}


@app.post("/feedback")
def feedback(body: FeedbackIn):
    if body.rating not in (1, -1):
        raise HTTPException(422, "rating must be 1 or -1")
    if not db.add_feedback(body.message_id, body.rating, body.comment):
        raise HTTPException(404, "message_id not found")
    return {"status": "saved"}


@app.get("/stats")
def stats(x_admin_token: Optional[str] = Header(None)):
    token = CONFIG.get("admin_token")
    if token and x_admin_token != token:
        raise HTTPException(401, "Invalid admin token")
    return db.stats()
