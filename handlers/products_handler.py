import os
import re
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

from langchain_google_genai import GoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from models.state_models import InventoryState, MongoQuery


# ✅ Gemini Model Setup
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)


def products_handler(state: InventoryState) -> InventoryState:
    """Build a MongoDB query for the Product collection"""

    user_query = state["user_query"]
    owner_id = state["owner_id"]

    now = datetime.now(timezone.utc)
    today = now.date()

    parser = PydanticOutputParser(pydantic_object=MongoQuery)
    format_instructions = parser.get_format_instructions()

    prompt = f"""
You are a MongoDB query generator for a shop inventory assistant.

Today's date (ISO 8601, UTC) is: "{today}".

You ONLY handle queries related to the Products collection.

Product collection ("products") schema:
- owner: String
- name: String
- category: String
- actualPrice: Number
- sellingPrice: Number
- quantity: Number
- reorderLevel: Number
- supplier: String
- expirationDate: Date
- dateAdded: Date
- dateUpdated: Date

Rules:
- Every filter MUST include: {{ "owner": "{owner_id}" }}
- Create ONE MongoDB find filter.
- Use ONLY listed field names.
- You may use $gt, $lt, $gte, $lte, $and, $or, $regex.

Return ONLY valid JSON using this schema:
{format_instructions}

User message:
{user_query}
"""

    try:
        raw_msg = model.invoke(prompt)
        raw_text = raw_msg.content if hasattr(raw_msg, "content") else str(raw_msg)

        mongo_query: MongoQuery = parser.parse(raw_text)
        filter_obj = mongo_query.filter

        # Always enforce owner
        filter_obj["owner"] = owner_id

        query_lower = user_query.lower()

        # 🔥 1️⃣ Expired Products
        if "expired" in query_lower:
            filter_obj["expirationDate"] = {"$lt": now}

        # 🔥 2️⃣ Expiring Soon (Dynamic Days Detection)
        elif "expire" in query_lower or "expiring" in query_lower:
            days_match = re.search(r"\d+", query_lower)
            days = int(days_match.group()) if days_match else 30

            future_date = now + timedelta(days=days)

            filter_obj["expirationDate"] = {
                "$gte": now,
                "$lte": future_date
            }

        return {
            "mongo_query": filter_obj,
            "collection": "products"
        }

    except Exception as e:
        print("Products Handler Error:", e)

        # Safe fallback
        return {
            "mongo_query": {"owner": owner_id},
            "collection": "products"
        }