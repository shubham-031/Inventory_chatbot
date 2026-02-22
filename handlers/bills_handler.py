import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import GoogleGenerativeAI
from models.state_models import InventoryState, MongoQuery
import re

# Load environment variables
load_dotenv()

# ✅ Correct model + API key  
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)


def bills_handler(state: InventoryState) -> InventoryState:
    """Build a MongoDB query for the Bill collection"""

    user_query = state["user_query"]
    owner_id = state["owner_id"]

    now = datetime.now(timezone.utc)
    today = now.date()
    start_of_today = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    end_of_today = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)

    parser = PydanticOutputParser(pydantic_object=MongoQuery)
    format_instructions = parser.get_format_instructions()

    prompt = f"""
You are a MongoDB query generator for a shop billing assistant.

Bill collection ("bills") schema:
- owner: String (REQUIRED)
- customerName: String
- billNumber: String
- date: Date
- phoneNumber: String
- deposit: Number
- customerId: String
- items: Array
- grandTotal: Number
- netQuantity: Number

IMPORTANT:
- Every filter MUST include: {{ "owner": "{owner_id}" }}
- Use ONLY these field names
- For time-based filters, use $gte, $lte, $gt, $lt on 'date'
- DO NOT include sort/limit/projection

Return ONLY valid JSON using this schema:
{format_instructions}

User message:
{user_query}
"""

    try:
        raw_msg = model.invoke(prompt)
        raw_text = raw_msg.content if hasattr(raw_msg, "content") else str(raw_msg)

        bill_query: MongoQuery = parser.parse(raw_text)
        filter_obj = bill_query.filter or {}

        filter_obj["owner"] = owner_id
        model_set_date = "date" in filter_obj

        if ("today" in user_query.lower()) and not model_set_date:
            filter_obj["date"] = {"$gte": start_of_today, "$lte": end_of_today}

        if not model_set_date:
            m = re.search(r"last\s+(\d+)\s+day", user_query.lower())
            if m:
                n_days = int(m.group(1))
                start_date = now - timedelta(days=n_days)
                filter_obj["date"] = {"$gte": start_date, "$lte": now}

        return {"mongo_query": filter_obj, "collection": "bills"}

    except Exception:
        # Safe fallback
        return {
            "mongo_query": {"owner": owner_id},
            "collection": "bills"
        }