import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from langchain_google_genai import GoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from models.state_models import InventoryState, IntentExtractor


# ✅ Correct Model + Explicit API Key
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",   # safest working model
    api_key=os.getenv("GEMINI_API_KEY")
)


def supervisor_router(state: InventoryState) -> InventoryState:
    """Router node: detects high-level intent from user_query"""

    user_query = state["user_query"]
    summary = state.get("response", "")
    db_results = state.get("db_results", "")

    parser = PydanticOutputParser(pydantic_object=IntentExtractor)
    format_instructions = parser.get_format_instructions()

    prompt = f"""
You are an intent classifier for a small shop inventory assistant.

Your job:
- Read the user's message.
- Choose exactly ONE intent from this list:
  - "products"
  - "suppliers"
  - "bills"
  - "customers"
  - "analytics"
  - "chitchat"

Rules:
- Always return exactly one of these words as the value of "intent".
- If unsure, pick the closest intent. 

Return the result using this JSON schema:
{format_instructions}

Previous summary (if any): {summary}
Database results (if any): {db_results}

User message:
{user_query}
"""

    try:
        raw_msg = model.invoke(prompt)
        raw_text = raw_msg.content if hasattr(raw_msg, "content") else str(raw_msg)

        intent_obj: IntentExtractor = parser.parse(raw_text)

        return {"intent": intent_obj.intent}

    except Exception as e:
        # Safe fallback
        return {"intent": "chitchat"}