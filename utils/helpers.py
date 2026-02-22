"""
Helper Functions
Response generation and database execution
"""
from typing import Dict, Any, List
from datetime import datetime
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from db.mongo_executor import MongoExecutor

# Initialize Gemini model
model = GoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)


def executor_node(state) -> Dict:
    """
    Execute MongoDB query and return results
    
    Args:
        state: Current state with mongo_query and collection
        
    Returns:
        dict: Updated state with db_results
    """
    mongo = MongoExecutor()
    results: Dict[str, List[Dict[str, Any]]] = {}

    mongo_query = state.get("mongo_query") or {}
    collection = state.get("collection")
    mongo_filter: Dict[str, Any] = mongo_query
    
    print(f"\n🔍 EXECUTOR DEBUG:")
    print(f"   Collection: {collection}")
    print(f"   Filter: {mongo_filter}")

    if not collection:
        print("   ⚠️ No collection specified")
        return {"db_results": results}

    owner_id = state.get("owner_id")
    if isinstance(mongo_filter, dict) and owner_id:
        mongo_filter.setdefault("owner", owner_id)

    print(f"   Final Filter: {mongo_filter}")

    # Execute the query
    db_result = mongo.execute_single(collection, mongo_filter, owner_id)
    
    print(f"   ✅ Results Count: {len(db_result)}")
    if db_result:
        print(f"   Sample: {list(db_result[0].keys())}")
    
    results[collection] = db_result

    return {"db_results": results}


def response_node(state) -> Dict:
    """
    Generate natural language response from DB results
    
    Args:
        state: Current state with user_query and db_results
        
    Returns:
        dict: Updated state with response
    """
    user_query = state.get("user_query", "")
    db_results: Dict[str, Any] = state.get("db_results", {}) or {}
    
    print(f"\n📝 RESPONSE NODE DEBUG:")
    print(f"   Query: {user_query}")
    
    # Count total items
    total_items = 0
    for collection, items in db_results.items():
        if isinstance(items, list):
            total_items += len(items)
            print(f"   {collection}: {len(items)} items")
    
    # Create detailed prompt
    prompt = f"""You are a helpful inventory assistant for a retail shop.

User asked: {user_query}

Database returned this data:
{db_results}

INSTRUCTIONS:
1. If data is empty (like {{"products": []}}), say: "No data found. Your database might be empty."
2. If data exists, provide a clear, formatted response with:
   - Product names, quantities, prices
   - Use bullet points or numbered lists
   - Include relevant details (stock, expiry, etc.)
3. Be concise but informative (2-5 sentences max)
4. For greetings, say: "Hi! Ask me about products, sales, bills, or analytics."

ONLY use the data provided above. Do NOT invent information.

Your response:"""
    
    try:
        llm_response = model.invoke(prompt)
        text = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        
        final_response = text.strip()
        
        # Fallback for empty data
        if total_items == 0 and "no data" not in final_response.lower():
            final_response = "No data found for this query. Your database might be empty or contains no matching records."
        
        print(f"   ✅ Response: {final_response[:100]}...")
        
        return {"response": final_response}
        
    except Exception as e:
        print(f"❌ Error in response_node: {e}")
        return {"response": f"Error generating response: {str(e)}"}


def chitchat_node(state) -> Dict:
    """
    Handle casual conversation and greetings
    
    Args:
        state: Current state with user_query
        
    Returns:
        dict: Updated state with response
    """
    user_msg = state.get("user_query", "")
    last_summary = state.get("response", "")
    db_results = state.get("db_results", "")

    CHITCHAT_PROMPT = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a friendly inventory chatbot for a small grocery shop. 
            
You handle:
1) Greetings (hi, hello, good morning, etc.)
2) Simple follow-up questions based on previous answers

If user greets, respond warmly and ask how you can help with inventory, bills, suppliers, or analytics.
If user asks about previous answer, use the context below.
Do not invent data - only use what's provided.

Keep responses short and friendly (1-2 sentences)."""
        ),
        (
            "human",
            """Previous answer (if any):
{previous_answer}

User message:
{user_message}

Database results (if any):
{db_results}"""
        ),
    ])

    prompt = CHITCHAT_PROMPT.format_messages(
        previous_answer=last_summary,
        user_message=user_msg,
        db_results=db_results,
    )

    try:
        llm_response = model.invoke(prompt)
        text = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        
        return {"response": text.strip()}
        
    except Exception as e:
        print(f"❌ Error in chitchat_node: {e}")
        return {"response": "Hello! How can I help you with your inventory today?"}