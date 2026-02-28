import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

from langchain_google_genai import GoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from models.state_models import InventoryState, IntentExtractor


# ================== GEMINI MODEL ==================
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)


# ================== ROUTER FUNCTION ==================
def supervisor_router(state: InventoryState) -> InventoryState:
    """
    Intelligent intent router for Smart Inventory AI
    Uses:
    1. Rule-based override (fast + accurate)
    2. Gemini fallback classification
    """

    user_query = state.get("user_query", "").lower()

    # ==========================================================
    # 🔥 1️⃣ RULE-BASED INTENT OVERRIDE (MOST IMPORTANT FIX)
    # ==========================================================

    # --- Bills / Sales ---
    if any(word in user_query for word in [
        "sale", "sales", "revenue", "income", "bill",
        "today sale", "total sale", "last 7 days",
        "aaj", "kal", "kamai", "vikri"
    ]):
        state["intent"] = "bills"
        return state

    # --- Products ---
    if any(word in user_query for word in [
        "product", "stock", "inventory",
        "low stock", "expired", "quantity",
        "items", "restock"
    ]):
        state["intent"] = "products"
        return state

    # --- Suppliers ---
    if any(word in user_query for word in [
        "supplier", "payment", "deposit",
        "outstanding", "balance"
    ]):
        state["intent"] = "suppliers"
        return state

    # --- Customers ---
    if any(word in user_query for word in [
        "customer", "visit", "purchase",
        "buyer"
    ]):
        state["intent"] = "customers"
        return state

    # --- Analytics ---
    if any(word in user_query for word in [
        "analysis", "trend", "report",
        "performance", "profit",
        "comparison", "growth"
    ]):
        state["intent"] = "analytics"
        return state

    # ==========================================================
    # 🧠 2️⃣ GEMINI LLM CLASSIFICATION (FALLBACK)
    # ==========================================================

    parser = PydanticOutputParser(pydantic_object=IntentExtractor)
    format_instructions = parser.get_format_instructions()

    prompt = f"""
You are an intent classifier for a grocery shop inventory assistant.

Intent meanings:

- "products" → Questions about stock, inventory, expired items, low stock.
- "suppliers" → Questions about suppliers, payments, balances.
- "bills" → Questions about sales, revenue, bills, income.
- "customers" → Questions about customers and visits.
- "analytics" → Business reports, trends, comparisons, profit analysis.
- "chitchat" → Greetings or casual talk.

IMPORTANT:
- Never classify business questions as chitchat.
- Sales or revenue questions must be classified as "bills".

Return ONLY valid JSON using this schema:
{format_instructions}

User message:
{user_query}
"""

    try:
        raw_msg = model.invoke(prompt)
        raw_text = raw_msg.content if hasattr(raw_msg, "content") else str(raw_msg)

        intent_obj: IntentExtractor = parser.parse(raw_text)

        state["intent"] = intent_obj.intent
        return state        

    except Exception:
        # Safe fallback
        state["intent"] = "chitchat"
        return state  