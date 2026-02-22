import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

from langchain_google_genai import GoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from models.state_models import InventoryState, MongoQuery


# ✅ Correct model + API key
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)


def products_handler(state: InventoryState) -> InventoryState:
    """Build a MongoDB query for the Product collection"""

    user_query = state["user_query"]
    owner_id = state["owner_id"]

    today = datetime.now(timezone.utc).date()
    end_of_yesterday = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)

    parser = PydanticOutputParser(pydantic_object=MongoQuery)
    format_instructions = parser.get_format_instructions()

    prompt = f"""
You are a MongoDB query generator for a shop inventory assistant.

Today's date (ISO 8601, UTC) is: "{end_of_yesterday}".

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
- For expired products use:
  {{ "expirationDate": {{ "$lt": "{end_of_yesterday}" }} }}

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
        filter_obj["owner"] = owner_id

        if "expire" in user_query.lower():
            filter_obj["expirationDate"] = {"$lt": end_of_yesterday}

        return {"mongo_query": filter_obj, "collection": "products"}

    except Exception:
        # Safe fallback
        return {
            "mongo_query": {"owner": owner_id},
            "collection": "products"
        }