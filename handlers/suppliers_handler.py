import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from models.state_models import InventoryState, MongoQuery

# Load environment variables
load_dotenv()

# ✅ Correct model + API key
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)


def suppliers_handler(state: InventoryState) -> InventoryState:
    """Build a MongoDB query for the Supplier collection"""

    user_query = state["user_query"]
    owner_id = state["owner_id"]
    today = datetime.now(timezone.utc).date().isoformat()

    parser = PydanticOutputParser(pydantic_object=MongoQuery)
    format_instructions = parser.get_format_instructions()

    prompt = f"""
You are a MongoDB query generator for a shop supplier assistant.

Today's date: "{today}"

Supplier collection ("suppliers") schema:
- owner: String (REQUIRED)
- supplierName: String
- totalPayment: String
- depositAmount: String
- Date: String
- createdAt: Date
- updatedAt: Date

IMPORTANT:
- Every filter MUST include: {{ "owner": "{owner_id}" }}
- Use ONLY these field names
- DO NOT include sort/limit/projection

Return ONLY valid JSON using this schema:
{format_instructions}

User message:
{user_query}
"""

    try:
        raw_msg = model.invoke(prompt)
        raw_text = raw_msg.content if hasattr(raw_msg, "content") else str(raw_msg)

        mongo_query: MongoQuery = parser.parse(raw_text)
        filter_obj = mongo_query.filter or {}

        filter_obj["owner"] = owner_id

        return {"mongo_query": filter_obj, "collection": "suppliers"}

    except Exception:
        # Safe fallback
        return {
            "mongo_query": {"owner": owner_id},
            "collection": "suppliers"
        }