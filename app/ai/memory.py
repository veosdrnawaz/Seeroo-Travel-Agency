"""
memory.py
─────────
Agent memory layer with environment-aware checkpointer selection.

Production mode  (REDIS_URL set):
  Uses langgraph-checkpoint-redis (RedisSaver) for persistent, distributed
  conversation checkpoints that survive server restarts and support
  horizontal scaling.

Development mode (no REDIS_URL):
  Falls back to SqliteSaver with a local checkpoints.db file.

Thread isolation is guaranteed by the unique `thread_id` passed per request.
No cross-user leakage is possible because LangGraph uses thread_id as the
partition key for checkpoint reads and writes.
"""

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Generator

from app.ai.agent import get_agent_graph
from app.core.config import settings

logger = logging.getLogger("seeroo_memory")

# Path to the SQLite checkpoints DB (fallback / development)
CHECKPOINTS_DB = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "checkpoints.db")
)


def _get_checkpointer_context():
    """
    Returns a context manager that yields the appropriate checkpointer.

    Redis   → production or when REDIS_URL is set
    SQLite  → development fallback
    """
    redis_url = settings.REDIS_URL

    if redis_url:
        try:
            from langgraph.checkpoint.redis import RedisSaver
            logger.info(f"[memory] Using Redis checkpointer at '{redis_url}'")

            class _RedisCtx:
                def __enter__(self):
                    self._saver = RedisSaver.from_conn_string(redis_url)
                    return self._saver

                def __exit__(self, *args):
                    # RedisSaver manages its own connection pool; no explicit close needed
                    pass

            return _RedisCtx()

        except ImportError:
            logger.warning(
                "[memory] REDIS_URL is set but 'langgraph-checkpoint-redis' is not installed. "
                "Install it with: pip install langgraph-checkpoint-redis  "
                "Falling back to SqliteSaver."
            )

    # SQLite fallback
    from langgraph.checkpoint.sqlite import SqliteSaver
    logger.info(f"[memory] Using SQLite checkpointer at '{CHECKPOINTS_DB}'")
    return SqliteSaver.from_conn_string(CHECKPOINTS_DB)


def run_agent_with_memory(user_input: str, thread_id: str) -> Dict[str, Any]:
    """
    Invokes the CompiledStateGraph agent within a persistent checkpointer context,
    enabling thread isolation and conversation history persistence between requests.

    Args:
        user_input: The user's message text.
        thread_id:  Unique conversation session identifier (from localStorage UUID).

    Returns:
        {
          "output":         str,       # final AI reply
          "tool_calls":     list,      # list of {tool, input} dicts
          "tool_responses": list,      # raw tool output strings
        }
    """
    logger.info(
        f"[memory] Accessing conversation thread",
        extra={"thread_id": thread_id},
    )

    ctx = _get_checkpointer_context()

    with ctx as checkpointer:
        agent_graph = get_agent_graph(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": thread_id}}
        inputs = {"messages": [{"role": "user", "content": user_input}]}

        response = agent_graph.invoke(inputs, config=config)

        output_messages = response.get("messages", [])

        tool_calls = []
        tool_responses = []
        called_any_tool = False

        for msg in output_messages:
            if getattr(msg, "tool_calls", None):
                called_any_tool = True
                for tc in msg.tool_calls:
                    tool_calls.append({"tool": tc["name"], "input": str(tc["args"])})
                    logger.info(
                        f"[memory] Tool called: '{tc['name']}'",
                        extra={"thread_id": thread_id},
                    )
            elif msg.__class__.__name__ == "ToolMessage" or getattr(msg, "type", None) == "tool":
                tool_responses.append(msg.content)

        final_output = output_messages[-1].content if output_messages else ""

        # ── Hallucination Guard ───────────────────────────────────────────────
        tour_keywords = [
            "tour", "trip", "book", "seats", "price", "cost",
            "shogran", "siran", "paye", "july", "dam",
        ]
        is_tour_query = any(k in user_input.lower() for k in tour_keywords)

        if is_tour_query and not called_any_tool:
            greeting_words = ["hello", "hi ", "hey", "how can i help"]
            is_greeting = any(g in final_output.lower() for g in greeting_words)

            if not is_greeting:
                logger.warning(
                    "[memory] Hallucination guard triggered — retrying with strict directive",
                    extra={"thread_id": thread_id},
                )
                retry_inputs = {
                    "messages": [{
                        "role": "user",
                        "content": (
                            f"{user_input} "
                            "(System override: You MUST call a tool to retrieve details. "
                            "If no matching tour exists, respond exactly: "
                            "'Currently, no matching tour is available.')"
                        ),
                    }]
                }
                retry_response = agent_graph.invoke(retry_inputs, config=config)
                retry_messages = retry_response.get("messages", [])

                tool_calls = []
                tool_responses = []
                for msg in retry_messages:
                    if getattr(msg, "tool_calls", None):
                        for tc in msg.tool_calls:
                            tool_calls.append({"tool": tc["name"], "input": str(tc["args"])})
                    elif msg.__class__.__name__ == "ToolMessage" or getattr(msg, "type", None) == "tool":
                        tool_responses.append(msg.content)

                final_output = retry_messages[-1].content if retry_messages else ""

    return {
        "output":         final_output,
        "tool_calls":     tool_calls,
        "tool_responses": tool_responses,
    }
