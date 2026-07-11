"""
chat.py
───────
POST /api/v1/chat — AI Booking Agent entrypoint.

Features:
  - Redis sliding-window rate limiter (falls back to in-memory on dev).
  - Structured JSON logging with thread_id context.
  - Booking ID extraction from tool responses.
  - Clean error shielding (no raw tracebacks to client).
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.ai.memory import run_agent_with_memory
from app.core.config import settings

logger = logging.getLogger("seeroo_chat_route")
router = APIRouter(prefix=settings.API_PREFIX, tags=["Chat"])

# ── Rate Limiter Configuration ────────────────────────────────────────────────
RATE_LIMIT_WINDOW  = 60   # seconds
RATE_LIMIT_MAX     = 20   # requests per window per thread

# In-memory fallback store (used in dev when Redis is unavailable)
_IN_MEMORY_RATE_STORE: Dict[str, list] = {}


def _check_rate_limit_redis(thread_id: str) -> bool:
    """
    Redis sliding-window rate limiter using sorted sets.
    Returns True if request is allowed, False if rate limit exceeded.
    """
    import redis as redis_lib

    client = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
    now = time.time()
    key = f"rl:chat:{thread_id}"

    pipe = client.pipeline()
    pipe.zremrangebyscore(key, 0, now - RATE_LIMIT_WINDOW)   # purge expired
    pipe.zadd(key, {str(now): now})                          # add current
    pipe.zcard(key)                                          # count
    pipe.expire(key, RATE_LIMIT_WINDOW + 5)                  # TTL cleanup
    _, _, count, _ = pipe.execute()

    return count <= RATE_LIMIT_MAX


def _check_rate_limit_memory(thread_id: str) -> bool:
    """
    In-memory sliding-window rate limiter (development fallback).
    NOT safe for multi-process deployments.
    """
    now = time.time()
    if thread_id not in _IN_MEMORY_RATE_STORE:
        _IN_MEMORY_RATE_STORE[thread_id] = []

    _IN_MEMORY_RATE_STORE[thread_id] = [
        t for t in _IN_MEMORY_RATE_STORE[thread_id]
        if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_IN_MEMORY_RATE_STORE[thread_id]) >= RATE_LIMIT_MAX:
        return False

    _IN_MEMORY_RATE_STORE[thread_id].append(now)
    return True


def check_rate_limit(thread_id: str) -> bool:
    """
    Routes to Redis or in-memory limiter based on environment config.
    Returns False if rate limited.
    """
    if settings.REDIS_URL:
        try:
            return _check_rate_limit_redis(thread_id)
        except Exception as redis_err:
            logger.warning(
                f"[rate_limit] Redis error — falling back to in-memory limiter: {redis_err}",
                extra={"thread_id": thread_id},
            )
            return _check_rate_limit_memory(thread_id)

    return _check_rate_limit_memory(thread_id)


# ── Request / Response Schemas ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    thread_id: str = Field(..., min_length=2, description="Unique conversation session identifier")
    message:   str = Field(..., min_length=1, max_length=2000, description="User message text")


class ChatResponse(BaseModel):
    reply:                str
    requires_confirmation: bool
    booking_id:           Optional[str] = None
    error:                Optional[Dict[str, Any]] = None


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Public entrypoint for the AI Travel Booking Agent.
    Validates rate limits, runs the agent with persistent memory,
    and returns a structured response hiding internal tool execution details.
    """
    thread_id = payload.thread_id
    message   = payload.message

    # 1. Rate limiting
    allowed = check_rate_limit(thread_id)
    if not allowed:
        logger.warning(
            "[chat] Rate limit exceeded",
            extra={"thread_id": thread_id, "route": "/api/v1/chat"},
        )
        return ChatResponse(
            reply="Rate limit exceeded. Please wait a moment before sending more messages.",
            requires_confirmation=False,
            error={"code": "RATE_LIMIT_EXCEEDED",
                   "message": f"Maximum {RATE_LIMIT_MAX} requests per {RATE_LIMIT_WINDOW}s per session."},
        )

    # 2. Run agent
    try:
        logger.info(
            "[chat] Invoking agent",
            extra={"thread_id": thread_id, "route": "/api/v1/chat"},
        )
        res = run_agent_with_memory(message, thread_id)

        reply         = res["output"]
        tool_calls    = res["tool_calls"]
        tool_responses = res["tool_responses"]

        # 3. Extract booking_id from tool responses
        booking_id = None
        for resp in tool_responses:
            try:
                data = json.loads(resp)
                if data.get("status") == "success" and "booking_id" in data:
                    booking_id = data["booking_id"]
                    logger.info(
                        "[chat] Booking confirmed",
                        extra={"thread_id": thread_id, "booking_id": booking_id},
                    )
                    break
            except Exception:
                continue

        # 4. Determine if price confirmation is pending
        requires_confirmation = False
        if not booking_id:
            for tc in tool_calls:
                if tc["tool"] == "calculate_price":
                    requires_confirmation = True
                    break

        return ChatResponse(
            reply=reply,
            requires_confirmation=requires_confirmation,
            booking_id=booking_id,
            error=None,
        )

    except Exception as exc:
        logger.error(
            "[chat] Internal agent error",
            extra={"thread_id": thread_id, "error": str(exc)},
            exc_info=True,
        )
        return ChatResponse(
            reply="An unexpected system error occurred. Please try again later.",
            requires_confirmation=False,
            error={"code": "INTERNAL_AGENT_ERROR", "message": str(exc)},
        )
