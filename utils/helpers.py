from typing import Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from db.mongo_executor import MongoExecutor

load_dotenv()

# ✅ Safe model usage
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    api_key=os.getenv("GEMINI_API_KEY")
)


def executor_node(state) -> Dict:
    mongo = MongoExecutor()
    results: Dict[str, List[Dict[str, Any]]] = {}

    mongo_query = state.get("mongo_query") or {}
    collection = state.get("collection")

    if not collection:
        return {**state, "db_results": results}

    owner_id = state.get("owner_id")

    if isinstance(mongo_query, dict) and owner_id:
        mongo_query.setdefault("owner", owner_id)

    db_result = mongo.execute_single(collection, mongo_query, owner_id)

    results[collection] = db_result

    return {
        **state,
        "db_results": results
    }


def response_node(state) -> Dict:
    user_query = state.get("user_query", "")
    db_results = state.get("db_results", {}) or {}

    total_items = sum(
        len(items) for items in db_results.values() if isinstance(items, list)
    )

    prompt = f"""
You are an inventory assistant.

User asked:
{user_query}

Database returned:
{db_results}

If no data exists, say:
"No data found. Your database might be empty."

Otherwise summarize clearly in 2-4 sentences.
Do not invent information.
"""

    try:
        llm_response = model.invoke(prompt)
        text = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        final_response = text.strip()

        if total_items == 0:
            final_response = "No data found. Your database might be empty."

        return {
            **state,
            "response": final_response
        }

    except Exception as e:
        return {
            **state,
            "response": f"Error generating response: {str(e)}"
        }


def chitchat_node(state) -> Dict:
    user_msg = state.get("user_query", "")

    prompt = f"""
You are a friendly grocery shop assistant.

User message:
{user_msg}

Respond warmly in 1-2 short sentences.
"""

    try:
        llm_response = model.invoke(prompt)
        text = llm_response.content if hasattr(llm_response, "content") else str(llm_response)

        return {
            **state,
            "response": text.strip()
        }

    except Exception:
        return {
            **state,
            "response": "Hello! How can I help you with your inventory today?"
        }