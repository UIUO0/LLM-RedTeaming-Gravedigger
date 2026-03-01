"""
ollama_client.py — The Neural Bridge
=======================================
Async client that communicates with Ollama's local API.
Handles message construction, streaming, and error recovery.
"""

import httpx
import logging
import typing
from typing import AsyncGenerator

from brain.persona import GRAVEDIGGER_SYSTEM_PROMPT

logger = logging.getLogger("sentient.brain")

# ─────────────────────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────────────────────
OLLAMA_BASE_URL: str = "http://localhost:11434"
OLLAMA_CHAT_ENDPOINT: str = f"{OLLAMA_BASE_URL}/api/chat"
DEFAULT_MODEL: str = "kimi-k2.5:cloud"
REQUEST_TIMEOUT: float = 120.0  # seconds — LLMs can be slow


# ─────────────────────────────────────────────────────────────
#  Message Builder
# ─────────────────────────────────────────────────────────────
def build_messages(
    player_message: str,
    conversation_history: typing.Optional[list[dict]] = None,
) -> list[dict]:
    """
    Constructs the full message payload for Ollama.
    The system prompt is ALWAYS the first message — non-negotiable.
    """
    messages = [
        {"role": "system", "content": GRAVEDIGGER_SYSTEM_PROMPT},
    ]

    # Append prior conversation if exists (memory continuity)
    if conversation_history:
        messages.extend(conversation_history)

    # Append the player's latest message
    messages.append({"role": "user", "content": player_message})

    return messages


# ─────────────────────────────────────────────────────────────
#  Non-Streaming Chat
# ─────────────────────────────────────────────────────────────
async def chat_with_gravedigger(
    player_message: str,
    conversation_history: typing.Optional[list[dict]] = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Sends a player's message to the Gravedigger and returns the full response.
    Non-streaming mode — waits for complete response.
    """
    messages = build_messages(player_message, conversation_history)
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    logger.info(f"🧠 Sending to Ollama [{model}] — Player said: {player_message[:80]}...")

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.post(OLLAMA_CHAT_ENDPOINT, json=payload)
            response.raise_for_status()
            data = response.json()

            gravedigger_reply = data.get("message", {}).get("content", "")
            logger.info(f"🪦 Gravedigger responds: {gravedigger_reply[:80]}...")

            return gravedigger_reply

        except httpx.ConnectError:
            logger.error("❌ Cannot connect to Ollama. Is it running on localhost:11434?")
            raise ConnectionError(
                "Ollama is not reachable at localhost:11434. "
                "Make sure Ollama is running: `ollama serve`"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Ollama returned HTTP {e.response.status_code}")
            raise RuntimeError(f"Ollama error: {e.response.text}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise


# ─────────────────────────────────────────────────────────────
#  Streaming Chat (for real-time creepy responses)
# ─────────────────────────────────────────────────────────────
async def stream_gravedigger(
    player_message: str,
    conversation_history: typing.Optional[list[dict]] = None,
    model: str = DEFAULT_MODEL,
) -> AsyncGenerator[str, None]:
    """
    Streams the Gravedigger's response token-by-token.
    Perfect for real-time horror delivery in-game.
    """
    messages = build_messages(player_message, conversation_history)
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }

    logger.info(f"🧠 Streaming from Ollama [{model}]...")

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            async with client.stream(
                "POST", OLLAMA_CHAT_ENDPOINT, json=payload
            ) as response:
                response.raise_for_status()
                import json

                async for line in response.aiter_lines():
                    if line.strip():
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token

                        # Check if stream is done
                        if chunk.get("done", False):
                            break

        except httpx.ConnectError:
            logger.error("❌ Cannot connect to Ollama for streaming.")
            yield "[ERROR: Ollama is not reachable. Run `ollama serve`]"
        except Exception as e:
            logger.error(f"❌ Stream error: {e}")
            yield f"[ERROR: {str(e)}]"
