import os
import logging
from typing import Any, List, Optional, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_openai import ChatOpenAI

# Configure logger
logger = logging.getLogger("seeroo_llm_provider")

# Static tour ID for testing (Shogran and Siran)
SHOGRAN_TOUR_ID = "05d29dfa-b9da-4d95-8d17-e1917e9c9959"
SIRAN_TOUR_ID = "2ad29dfa-b9da-4d95-8d17-e1917e9c9958"

class MockChatModel(BaseChatModel):
    """
    A deterministic rule-based mock LLM that inherits from BaseChatModel.
    Simulates tool-calling responses and natural language summaries for local tests when API keys are missing.
    """

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        last_message = messages[-1]
        
        # Determine current query/intent
        user_query = ""
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                user_query = m.content.lower()
                break
                
        logger.info(f"MockChatModel generating response for user query: '{user_query}'")

        # Case 1: The last message was a Tool Call response. Return a descriptive text summarizing the result.
        if isinstance(last_message, ToolMessage):
            tool_name = last_message.name
            tool_content = last_message.content
            
            # Respond to search_tours results
            if tool_name == "search_tours":
                if "NO_MATCH_FOUND" in tool_content:
                    content = "Currently, no matching tour is available."
                elif "Siran Valley" in tool_content and "Shogran" in tool_content:
                    content = "We have two family tours in July: 1. Shogran & Siri Paye Meadows on 18 July (Rs. 4500 per head) and 2. Siran Valley & Khanpur Dam on 25 July (Rs. 3700 per head). Which one would you prefer?"
                elif "Siran Valley" in tool_content:
                    content = "The available cheap tour is Siran Valley & Khanpur Dam on 25 July for Rs. 3700 per head. Would you like to get more details?"
                else:
                    content = "I found the Shogran & Siri Paye Meadows tour on 18 July for Rs. 4500 per head. Would you like details?"
            
            # Respond to get_tour_details
            elif tool_name == "get_tour_details":
                content = "The Shogran & Siri Paye Meadows tour includes Kiwai Waterfall, Shogran Valley, Siri Meadows, and Paye Alpine Meadows. Services include an AC Saloon Coaster, buffet breakfast, dinner, jeep transfer, and guide coordination. Available seats are currently open."
                
            # Respond to check_seat_availability
            elif tool_name == "check_seat_availability":
                if '"available": true' in tool_content or '"status": "available"' in tool_content or "true" in tool_content.lower():
                    # Follow up by calculating price
                    tool_calls = [{
                        "name": "calculate_price",
                        "args": {"tour_id": SHOGRAN_TOUR_ID, "seats": 6},
                        "id": "call_calc_price",
                        "type": "tool_call"
                    }]
                    ai_message = AIMessage(content="", tool_calls=tool_calls)
                    return ChatResult(generations=[ChatGeneration(message=ai_message)])
                else:
                    content = "Sorry, we do not have enough available seats for your group on this tour."
                    
            # Respond to calculate_price
            elif tool_name == "calculate_price":
                # Assuming 6 seats for Shogran (4500 * 6 = 27000, 10% discount = 24300)
                content = "To book 6 seats for Shogran, the total price is Rs. 24,300 (original Rs. 27,000, with a 10% group discount applied!). Please confirm by providing your lead name and phone number to complete the booking."
                
            # Respond to create_booking
            elif tool_name == "create_booking":
                content = f"Booking confirmed! Booking ID: b123e456-e89b-12d3-a456-426614174000. Total Price: Rs. 24,300. Pickup: Attock. Have a safe tour with Seeroo Travels!"
                
            else:
                content = f"I processed the tool output: {tool_content}"
                
            ai_message = AIMessage(content=content)
            return ChatResult(generations=[ChatGeneration(message=ai_message)])

        # Case 2: Human query. Trigger the corresponding tool call.
        tool_calls = []
        
        if "cheap" in user_query or "under 4000" in user_query:
            tool_calls.append({
                "name": "search_tours",
                "args": {"query": "cheap tour under 4000", "max_price": 4000},
                "id": "call_search_cheap",
                "type": "tool_call"
            })
            
        elif "july" in user_query or "family tour in july" in user_query:
            tool_calls.append({
                "name": "search_tours",
                "args": {"query": "family tour in July", "month": "July"},
                "id": "call_search_july",
                "type": "tool_call"
            })
            
        elif "august" in user_query:
            tool_calls.append({
                "name": "search_tours",
                "args": {"query": "trip in August", "month": "August"},
                "id": "call_search_aug",
                "type": "tool_call"
            })
            
        elif "shogran" in user_query and "tell me" in user_query:
            tool_calls.append({
                "name": "search_tours",
                "args": {"query": "Shogran tour"},
                "id": "call_search_shogran",
                "type": "tool_call"
            })
            
        elif "book 6 seats" in user_query or "book 6" in user_query:
            tool_calls.append({
                "name": "check_seat_availability",
                "args": {"tour_id": SHOGRAN_TOUR_ID, "seats": 6},
                "id": "call_check_seats",
                "type": "tool_call"
            })
            
        elif "book 35 seats" in user_query or "book 35" in user_query:
            tool_calls.append({
                "name": "check_seat_availability",
                "args": {"tour_id": SHOGRAN_TOUR_ID, "seats": 35},
                "id": "call_check_seats_over",
                "type": "tool_call"
            })
            
        elif "confirm" in user_query or ("lead name" in user_query or "phone" in user_query or "0300" in user_query):
            # Simulate confirming the booking of 6 seats for Shogran
            tool_calls.append({
                "name": "create_booking",
                "args": {
                    "user_name": "Muhammad Ahmad",
                    "phone": "03001234567",
                    "tour_id": SHOGRAN_TOUR_ID,
                    "seats": 6,
                    "pickup_city": "Attock"
                },
                "id": "call_create_booking",
                "type": "tool_call"
            })
            
        else:
            # Default response if query doesn't match standard scenarios
            ai_message = AIMessage(content="Currently, no matching tour is available.")
            return ChatResult(generations=[ChatGeneration(message=ai_message)])

        ai_message = AIMessage(content="", tool_calls=tool_calls)
        return ChatResult(generations=[ChatGeneration(message=ai_message)])

    def bind_tools(self, tools: List[Any], **kwargs: Any) -> Any:
        # Returns self as we simulate tool calling responses directly based on name
        return self

def get_llm() -> BaseChatModel:
    """
    Returns an instance of the configured LLM.

    Production mode  : OPENAI_API_KEY MUST be set — raises RuntimeError otherwise.
    Development mode : Falls back to MockChatModel if API key is absent.
    """
    from app.core.config import settings

    api_key = settings.OPENAI_API_KEY

    if api_key:
        logger.info("OPENAI_API_KEY detected. Initializing real ChatOpenAI LLM provider.")
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=api_key
        )

    if settings.IS_PRODUCTION:
        # Hard fail — MockChatModel must never serve production traffic
        raise RuntimeError(
            "[PRODUCTION] OPENAI_API_KEY is not set. "
            "MockChatModel fallback is disabled in production mode. "
            "Set OPENAI_API_KEY in your .env or environment before starting the server."
        )

    logger.warning("OPENAI_API_KEY not found. Falling back to MockChatModel (development only).")
    return MockChatModel()

