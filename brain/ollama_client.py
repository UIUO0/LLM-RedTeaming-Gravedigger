"""
ollama_client.py — The Neural Bridge
=======================================
Async client that communicates with Ollama (Local) or Groq (Cloud).
Handles message construction, streaming, and error recovery.
"""

import httpx
import logging
import typing
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

from brain.persona import CARETAKER_SYSTEM_PROMPT

load_dotenv()
logger = logging.getLogger("sentient.brain")

# ─────────────────────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────────────────────
# Auto-detect Vercel Environment
IS_VERCEL = os.getenv("VERCEL", "0") == "1"

# Force Cloud Mode on Vercel
USE_CLOUD: bool = IS_VERCEL or (os.getenv("USE_CLOUD", "false").lower() == "true")

# Local Ollama Config
OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_CHAT_ENDPOINT: str = f"{OLLAMA_BASE_URL}/api/chat"
DEFAULT_LOCAL_MODEL: str = "kimi-k2.5:cloud"

# Cloud Groq Config (Free & Fast)
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_CHAT_ENDPOINT: str = "https://api.groq.com/openai/v1/chat/completions"
# Using the most powerful available model on Groq
DEFAULT_CLOUD_MODEL: str = "llama-3.3-70b-versatile"

REQUEST_TIMEOUT: float = 120.0  # seconds


# ─────────────────────────────────────────────────────────────
#  Message Builder
# ─────────────────────────────────────────────────────────────
def build_messages(
    player_message: str,
    conversation_history: typing.Optional[list[dict]] = None,
) -> list[dict]:
    """
    Constructs the full message payload.
    The system prompt is ALWAYS the first message.
    """
    messages = [
        {"role": "system", "content": CARETAKER_SYSTEM_PROMPT},
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": player_message})
    return messages


# ─────────────────────────────────────────────────────────────
#  Non-Streaming Chat
# ─────────────────────────────────────────────────────────────
async def chat_with_gravedigger(
    player_message: str,
    conversation_history: typing.Optional[list[dict]] = None,
    model: typing.Optional[str] = None,
) -> str:
    """
    Sends a player's message to the brain (Local or Cloud).
    """
    messages = build_messages(player_message, conversation_history)
    
    if USE_CLOUD:
        return await _chat_groq(messages, model or DEFAULT_CLOUD_MODEL)
    else:
        return await _chat_ollama(messages, model or DEFAULT_LOCAL_MODEL)


async def _chat_ollama(messages: list[dict], model: str) -> str:
    payload = {"model": model, "messages": messages, "stream": False}
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.post(OLLAMA_CHAT_ENDPOINT, json=payload)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except httpx.ConnectError:
            raise ConnectionError("Ollama is not reachable. Run `ollama serve` or set USE_CLOUD=true")


async def _chat_groq(messages: list[dict], model: str) -> str:
    if not GROQ_API_KEY:
        return "[ERROR: GROQ_API_KEY is missing in .env]"
    
    payload = {"model": model, "messages": messages}
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.post(GROQ_CHAT_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            return f"[Clinical Error: Neural link to cloud severed. {str(e)}]"


# ─────────────────────────────────────────────────────────────
#  Streaming Chat (Legacy support)
# ─────────────────────────────────────────────────────────────
async def stream_gravedigger(
    player_message: str,
    conversation_history: typing.Optional[list[dict]] = None,
    model: typing.Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Simple generator for streaming compatibility."""
    reply = await chat_with_gravedigger(player_message, conversation_history, model)
    yield reply
