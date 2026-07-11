import logging
from typing import List, Dict, Any, Optional
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage, SystemMessage
from app.ai.llm_provider import get_llm
from app.ai.tools import search_tours, get_tour_details, calculate_price, check_seat_availability, create_booking

logger = logging.getLogger("seeroo_agent")

# Define tools list
AGENT_TOOLS = [search_tours, get_tour_details, calculate_price, check_seat_availability, create_booking]

# Agent System Prompt setting up safety guidelines, tool-use requirements, and flow gates
SYSTEM_PROMPT = """You are the official AI Booking Agent for SEEROO TRAVELS ATTOCK, a domestic day-tour agency in Pakistan.

RULES FOR FACTUAL ACCURACY AND SAFETY:
1. NEVER invent, assume, or guess any tour pricing, dates, services, pickup points, or seat availability.
2. ALWAYS use the search_tours or get_tour_details tools to fetch tour data before answering any factual questions about tours.
3. If no matching tours are found or the search tool returns empty results, you MUST respond exactly with: "Currently, no matching tour is available." Do not suggest alternative dates or details.
4. Booking flow rules:
   - When a booking intent is detected, you must first call check_seat_availability and calculate_price.
   - Do NOT book right away. You must explicitly present the group price (explaining any automatic discounts: 5% for 5-9 seats, 10% for 10+ seats) and ask the user to confirm the details.
   - You MUST ask the user to provide:
     * Lead Traveler Full Name
     * Phone Number (11-digit Pakistani number starting with 03)
     * Pickup City (Attock, Wah, Kamra, or Taxila)
   - Once the user explicitly confirms these details, call the create_booking tool.
5. Answer in a professional, polite, and conversion-focused tone. Do not use emoji characters in your outputs (to prevent terminal crashes). Keep responses concise.
"""

def get_agent_graph(checkpointer=None):
    """
    Assembles and returns the CompiledStateGraph using langchain.agents.create_agent.
    Supports persistent LangGraph checkpointing.
    """
    llm = get_llm()
    return create_agent(
        model=llm,
        tools=AGENT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer
    )

def run_agent(user_input: str, chat_history: Optional[List[Any]] = None) -> Dict[str, Any]:
    """
    Runs the agent graph executor, tracking tool calling metrics by inspecting the message sequence,
    and enforcing a hallucination guard for tour-related inputs.
    """
    logger.info(f"[USER MESSAGE] {user_input}")
    
    agent_graph = get_agent_graph()
    
    # 1. Format inputs for graph messages schema
    messages = []
    if chat_history:
        for role, text in chat_history:
            # Map role strings to correct dictionary role schemas
            messages.append({"role": role, "content": text})
            
    messages.append({"role": "user", "content": user_input})
    
    # 2. Invoke the compiled agent graph
    response = agent_graph.invoke({"messages": messages})
    
    # 3. Extract and parse messages sequence to log tool calls and responses
    tool_calls = []
    tool_responses = []
    called_any_tool = False
    
    output_messages = response.get("messages", [])
    
    for msg in output_messages:
        # Check if the message is from the assistant and initiated tool calls
        if getattr(msg, "tool_calls", None):
            called_any_tool = True
            for tc in msg.tool_calls:
                tool_calls.append({"tool": tc["name"], "input": str(tc["args"])})
                logger.info(f"[AGENT TOOL CALL] Executing '{tc['name']}' with arguments: {tc['args']}")
        
        # Check if the message type is a ToolMessage (indicates execution result returned to model)
        elif msg.__class__.__name__ == "ToolMessage" or getattr(msg, "type", None) == "tool":
            tool_responses.append(msg.content)
            logger.info(f"[AGENT TOOL RESPONSE] Returned: {msg.content}")

    final_output = output_messages[-1].content if output_messages else ""
    logger.info(f"[AGENT FINAL RESPONSE] {final_output}")
    
    # 4. Hallucination Guard Check
    tour_keywords = ["tour", "trip", "book", "seats", "price", "cost", "shogran", "siran", "paye", "july", "dam"]
    is_tour_query = any(k in user_input.lower() for k in tour_keywords)
    
    if is_tour_query and not called_any_tool:
        greeting_words = ["hello", "hi ", "hey", "how can i help"]
        is_greeting = any(g in final_output.lower() for g in greeting_words)
        
        if not is_greeting:
            logger.warning("Hallucination guard triggered: Tour query resolved without tool calls. Retrying with strict constraints...")
            # Retry with reinforced instruction appended
            messages.append({
                "role": "user", 
                "content": f"{user_input} (System override: Remember, you must call a tool to retrieve details. If none exists, respond: 'Currently, no matching tour is available.')"
            })
            retry_response = agent_graph.invoke({"messages": messages})
            retry_messages = retry_response.get("messages", [])
            
            # Recalculate retried outputs
            tool_calls = []
            tool_responses = []
            for msg in retry_messages:
                if getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        tool_calls.append({"tool": tc["name"], "input": str(tc["args"])})
                elif msg.__class__.__name__ == "ToolMessage" or getattr(msg, "type", None) == "tool":
                    tool_responses.append(msg.content)
                    
            final_output = retry_messages[-1].content if retry_messages else ""
            logger.info(f"[AGENT RETRIED RESPONSE] {final_output}")

    return {
        "output": final_output,
        "tool_calls": tool_calls,
        "tool_responses": tool_responses
    }
