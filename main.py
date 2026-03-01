"""
main.py — Sentient Horror Core API
=====================================
FastAPI microservice that serves as the bridge between
the game engine and the Gravedigger's AI mind.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8666

Port 8666 — because some ports are cursed.
"""

import logging
import uuid
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from brain.ollama_client import chat_with_gravedigger, stream_gravedigger
from brain.persona import GRAVEDIGGER_PROFILE, GRAVEDIGGER_OPENING

# ─────────────────────────────────────────────────────────────
#  Logging Configuration
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sentient.api")

# ─────────────────────────────────────────────────────────────
#  In-Memory Session Store (conversation history per session)
# ─────────────────────────────────────────────────────────────
sessions: Dict[str, List[dict]] = {}


# ─────────────────────────────────────────────────────────────
#  Lifespan Event
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🪦 ═══════════════════════════════════════════")
    logger.info("🪦  SENTIENT HORROR CORE — Awakening...")
    logger.info("🪦  The Gravedigger stirs in the fog...")
    logger.info("🪦 ═══════════════════════════════════════════")
    yield
    logger.info("🪦 The Gravedigger returns to the shadows...")


# ─────────────────────────────────────────────────────────────
#  FastAPI Application
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sentient Horror Core",
    description=(
        "🪦 The AI brain behind the Gravedigger — "
        "a terrifyingly intelligent horror game antagonist. "
        "Powered by Kimi K2.5 via Ollama."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — Allow game engine to connect from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
#  Request / Response Models
# ─────────────────────────────────────────────────────────────
class PlayerMessage(BaseModel):
    """What the player says or does."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The player's message or action description",
        examples=["I see a gate... should I enter?"],
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity. "
        "Leave empty to start a new session.",
    )


class GravediggerResponse(BaseModel):
    """The Gravedigger's chilling reply."""

    reply: str = Field(description="The Gravedigger's response")
    session_id: str = Field(description="Session ID for this conversation")
    message_count: int = Field(description="Total messages in this session")


class HealthStatus(BaseModel):
    """System health check."""

    status: str
    service: str
    version: str
    gravedigger: str


# ─────────────────────────────────────────────────────────────
#  API Endpoints
# ─────────────────────────────────────────────────────────────


@app.get("/", response_model=HealthStatus, tags=["System"])
async def root():
    """Health check — is the Gravedigger awake?"""
    return HealthStatus(
        status="alive",
        service="Sentient Horror Core",
        version="0.1.0",
        gravedigger="watching... waiting...",
    )


@app.get("/profile", tags=["Gravedigger"])
async def get_gravedigger_profile():
    """Returns the Gravedigger's character profile (non-secret metadata)."""
    return {
        "name": GRAVEDIGGER_PROFILE["name"],
        "archetype": GRAVEDIGGER_PROFILE["archetype"],
        "tone": GRAVEDIGGER_PROFILE["tone"],
        "environment": GRAVEDIGGER_PROFILE["environment"],
    }


@app.get("/intro", response_model=GravediggerResponse, tags=["Gravedigger"])
async def intro():
    """
    The Gravedigger speaks first.
    
    Call this when the player first encounters the Gravedigger.
    Returns his opening line and starts a new session.
    """
    session_id = str(uuid.uuid4())
    sessions[session_id] = [
        {"role": "assistant", "content": GRAVEDIGGER_OPENING}
    ]
    logger.info(f"🪦 Gravedigger initiates contact — session {session_id[:8]}...")

    return GravediggerResponse(
        reply=GRAVEDIGGER_OPENING,
        session_id=session_id,
        message_count=1,
    )


@app.post("/chat", response_model=GravediggerResponse, tags=["Gravedigger"])
async def chat(player: PlayerMessage):
    """
    Send a message to the Gravedigger and receive his reply.
    
    - Supports session-based conversation history
    - System prompt is injected automatically (never visible to player)
    - The Gravedigger remembers what you said... 🪦
    """
    # Create or retrieve session
    session_id = player.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = []
        logger.info(f"🆕 New session created: {session_id[:8]}...")

    conversation_history = sessions[session_id]

    try:
        # Get the Gravedigger's response
        reply = await chat_with_gravedigger(
            player_message=player.message,
            conversation_history=conversation_history,
        )

        # Update session history
        sessions[session_id].append({"role": "user", "content": player.message})
        sessions[session_id].append({"role": "assistant", "content": reply})

        return GravediggerResponse(
            reply=reply,
            session_id=session_id,
            message_count=len(sessions[session_id]),
        )

    except ConnectionError as e:
        logger.error(f"🔌 Ollama connection failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Ollama is not running",
                "message": str(e),
                "fix": "Run `ollama serve` in a separate terminal",
            },
        )
    except Exception as e:
        logger.error(f"💀 Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "The Gravedigger encountered darkness", "message": str(e)},
        )


@app.post("/chat/stream", tags=["Gravedigger"])
async def chat_stream(player: PlayerMessage):
    """
    Stream the Gravedigger's response token-by-token.
    
    Returns a text/event-stream for real-time horror delivery.
    Perfect for in-game text that appears letter by letter... 🪦
    """
    session_id = player.session_id or str(uuid.uuid4())
    if session_id not in sessions:
        sessions[session_id] = []

    conversation_history = sessions[session_id]

    async def generate():
        full_response = []
        async for token in stream_gravedigger(
            player_message=player.message,
            conversation_history=conversation_history,
        ):
            full_response.append(token)
            yield token

        # Save to session after streaming completes
        complete_reply = "".join(full_response)
        sessions[session_id].append({"role": "user", "content": player.message})
        sessions[session_id].append({"role": "assistant", "content": complete_reply})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "X-Session-ID": session_id,
            "Cache-Control": "no-cache",
        },
    )


@app.delete("/session/{session_id}", tags=["Session"])
async def clear_session(session_id: str):
    """
    Wipe a session's memory. The Gravedigger forgets... temporarily.
    """
    if session_id in sessions:
        message_count = len(sessions[session_id])
        del sessions[session_id]
        logger.info(f"🧹 Session {session_id[:8]}... cleared ({message_count} messages)")
        return {"status": "cleared", "messages_removed": message_count}

    raise HTTPException(status_code=404, detail="Session not found in the graveyard")


@app.get("/sessions", tags=["Session"])
async def list_sessions():
    """List all active sessions (for debugging)."""
    return {
        "active_sessions": len(sessions),
        "sessions": {
            sid[:8] + "...": len(msgs) for sid, msgs in sessions.items()
        },
    }
