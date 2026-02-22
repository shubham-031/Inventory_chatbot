"""
Analytics Tools Module
Provides analytics functions for sales, profit, and inventory insights
"""
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from db.mongo_client import mongo_client


# ==================== ANALYTICS TOOLS ====================

@tool
def get_sales(
    owner_id: str,
    date_scope: str = "today",
    specific_date: Optional[str] = None,
) -> Dict:
    """
    Get total sales (sum of grandTotal) and bill count for:
      - today
      - yesterday
      - a specific date (YYYY-MM-DD)
    
    Args:
        owner_id: Shop owner email
        date_scope: "today", "yesterday", or "specific_date"
        specific_date: Date in YYYY-MM-DD format (if date_scope is "specific_date")
    
    Returns:
        dict: Sales data with total_sales, bill_count, and date
    """
    if mongo_client.db is None:
        mongo_client.connect()

    bills = mongo_client.db["bills"]
    now = datetime.now(timezone.utc)

    # Decide target day
    if date_scope == "today":
        target = now
    elif date_scope == "yesterday":
        target = now - timedelta(days=1)
    elif date_scope == "specific_date" and specific_date:
        target = datetime.strptime(specific_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        target = now

    # Start/end of that day
    day_date = target.date()
    start_of_day = datetime.combine(day_date, datetime.min.time(), tzinfo=timezone.utc)
    end_of_day = datetime.combine(day_date, datetime.max.time(), tzinfo=timezone.utc)

    pipeline = [
        {
            "$match": {
                "owner": owner_id,
                "date": {"$gte": start_of_day, "$lte": end_of_day},
            }
        },
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": "$grandTotal"},
                "bill_count": {"$sum": 1},
            }
        },
    ]

    result = list(bills.aggregate(pipeline))
    if not result:
        return {
            "total_sales": 0,
            "bill_count": 0,
            "date": day_date.isoformat(),
        }

    doc = result[0]
    return {
        "total_sales": float(doc.get("total_sales", 0) or 0),
        "bill_count": int(doc.get("bill_count", 0) or 0),
        "date": day_date.isoformat(),
    }


@tool
def get_profit(
    owner_id: str,
    date_scope: str = "today",
    specific_date: Optional[str] = None,
) -> Dict:
    """
    Get profit and loss for a specific date.
    Profit = sum(grandTotal) - sum(actualPrice * quantity)
    
    Args:
        owner_id: Shop owner email
        date_scope: "today", "yesterday", or "specific_date"
        specific_date: Date in YYYY-MM-DD format
    
    Returns:
        dict: Profit data with profit, loss, revenue, cost, and bill_count
    """
    if mongo_client.db is None:
        mongo_client.connect()

    db = mongo_client.db
    bills = db["bills"]
    products_col = db["products"]

    now = datetime.now(timezone.utc)

    # Decide target day
    if date_scope == "today":
        target = now
    elif date_scope == "yesterday":
        target = now - timedelta(days=1)
    elif date_scope == "specific_date" and specific_date:
        target = datetime.strptime(specific_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        target = now

    day_date = target.date()
    start_of_day = datetime.combine(day_date, datetime.min.time(), tzinfo=timezone.utc)
    end_of_day = datetime.combine(day_date, datetime.max.time(), tzinfo=timezone.utc)

    # Load cost prices from products
    product_docs = list(
        products_col.find(
            {"owner": owner_id},
            {"name": 1, "actualPrice": 1, "_id": 0},
        )
    )
    cost_map = {
        p["name"]: float(p.get("actualPrice", 0) or 0)
        for p in product_docs
    }

    # Calculate revenue and cost
    cursor = bills.find(
        {
            "owner": owner_id,
            "date": {"$gte": start_of_day, "$lte": end_of_day},
        },
        {"grandTotal": 1, "items.productName": 1, "items.quantity": 1, "_id": 0},
    )

    total_revenue = 0.0
    total_cost = 0.0
    bill_count = 0

    for bill in cursor:
        bill_count += 1
        total_revenue += float(bill.get("grandTotal", 0) or 0)

        for item in bill.get("items", []):
            name = item.get("productName")
            qty = float(item.get("quantity", 0) or 0)
            unit_cost = cost_map.get(name, 0.0)
            total_cost += unit_cost * qty

    profit_val = total_revenue - total_cost

    return {
        "profit": profit_val if profit_val >= 0 else 0,
        "loss": -profit_val if profit_val < 0 else 0,
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "bill_count": bill_count,
        "date": day_date.isoformat(),
    }


@tool
def get_last_n_days_sales(owner_id: str, n_days: int) -> Dict:
    """
    Get sales summary for the last n_days (including today).
    
    Args:
        owner_id: Shop owner email
        n_days: Number of days to analyze
    
    Returns:
        dict: Daily sales breakdown with total and average
    """
    if mongo_client.db is None:
        mongo_client.connect()

    bills = mongo_client.db["bills"]
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=n_days - 1)).date()
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)

    pipeline = [
        {
            "$match": {
                "owner": owner_id,
                "date": {"$gte": start_dt, "$lte": now},
            }
        },
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$date"},
                    "month": {"$month": "$date"},
                    "day": {"$dayOfMonth": "$date"},
                },
                "total_sales": {"$sum": "$grandTotal"},
                "bill_count": {"$sum": 1},
            }
        },
        {
            "$sort": {
                "_id.year": 1,
                "_id.month": 1,
                "_id.day": 1,
            }
        },
    ]

    docs = list(bills.aggregate(pipeline))

    daily: List[Dict] = []
    total_sales_all = 0.0

    for d in docs:
        y = d["_id"]["year"]
        m = d["_id"]["month"]
        day = d["_id"]["day"]
        date_str = datetime(y, m, day).date().isoformat()

        day_sales = float(d.get("total_sales", 0) or 0)
        bill_count = int(d.get("bill_count", 0) or 0)

        total_sales_all += day_sales

        daily.append({
            "date": date_str,
            "total_sales": day_sales,
            "bill_count": bill_count,
        })

    if daily:
        best = max(daily, key=lambda x: x["total_sales"])
        best_day = {"date": best["date"], "total_sales": best["total_sales"]}
        avg_per_day = total_sales_all / len(daily)
    else:
        best_day = {"date": None, "total_sales": 0}
        avg_per_day = 0.0

    return {
        "daily": daily,
        "total_sales": total_sales_all,
        "avg_per_day": avg_per_day,
        "best_day": best_day,
        "window_days": n_days,
    }


@tool
def get_product_performance(
    owner_id: str,
    top_k: int = 5,
) -> Dict:
    """
    Get top selling products by quantity.
    
    Args:
        owner_id: Shop owner email
        top_k: Number of top products to return
    
    Returns:
        dict: Top selling products list
    """
    if mongo_client.db is None:
        mongo_client.connect()

    bills = mongo_client.db["bills"]

    pipeline = [
        {"$match": {"owner": owner_id}},
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.productName",
                "total_qty": {"$sum": "$items.quantity"},
                "total_revenue": {"$sum": "$items.total"},
            }
        },
        {"$sort": {"total_qty": -1, "total_revenue": -1}},
        {"$limit": top_k},
    ]
    
    top_docs = list(bills.aggregate(pipeline))
    top_selling = [
        {
            "productName": d["_id"],
            "total_qty": int(d.get("total_qty", 0) or 0),
            "total_revenue": float(d.get("total_revenue", 0) or 0),
        }
        for d in top_docs
    ]

    return {"top_selling": top_selling}


# List of all analytics tools
analytics_tools = [
    get_sales,
    get_profit,
    get_last_n_days_sales,
    get_product_performance,
]


# ==================== ANALYTICS WORKFLOW NODES ====================

# Initialize LLM with tools
analytics_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
).bind_tools(analytics_tools)


def analytics_llm_node(state) -> Dict:
    """
    Node that lets Gemini decide which analytics tool to call.
    
    Args:
        state: Current state with user_query and owner_id
        
    Returns:
        dict: Updated state with messages containing tool calls
    """
    user_query = state["user_query"]
    owner_id = state["owner_id"]

    system_prompt = (
        "You are an analytics assistant for a small grocery shop. "
        "You have access to tools that can fetch analytics from a MongoDB database. "
        "Always include the 'owner_id' argument when calling any tool.\n\n"
        "User can ask things like:\n"
        "- 'What is today's profit?'\n"
        "- 'How much did I sell in the last 10 days?'\n"
        "- 'Which products are not selling?'\n"
        "- 'Show top selling products'\n\n"
        "Your job is to choose the correct analytics tool and arguments."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Owner id: {owner_id}\nUser question: {user_query}"),
    ]

    ai_msg = analytics_llm.invoke(messages)
    
    print(f"\n🔍 ANALYTICS LLM NODE:")
    print(f"   Query: {user_query}")
    print(f"   Tool calls: {getattr(ai_msg, 'tool_calls', None)}")

    return {"messages": [ai_msg]}


def analytics_formatter_node(state) -> Dict:
    """
    Final step: Format analytics results into natural language.
    
    Args:
        state: Current state with messages containing tool results
        
    Returns:
        dict: Updated state with formatted response
    """
    user_query = state["user_query"]
    messages = state["messages"]

    # Find the last ToolMessage
    tool_output_text = None
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            tool_output_text = msg.content
            break

    if tool_output_text is None:
        tool_output_text = "{}"

    system_prompt = (
        "You are a grocery shop analytics assistant. "
        "You will receive analytics results in JSON format. "
        "Explain the answer in 2-4 clear sentences. "
        "Do NOT call any tools. Do NOT invent numbers. "
        "Format responses nicely with key metrics highlighted."
    )

    analytics_formatter_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
    )

    llm_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=(
                f"User question:\n{user_query}\n\n"
                f"Analytics JSON result:\n{tool_output_text}"
            )
        ),
    ]

    final_ai = analytics_formatter_llm.invoke(llm_messages)
    
    print(f"\n📊 ANALYTICS FORMATTER:")
    print(f"   Tool Output: {tool_output_text[:200]}...")
    print(f"   Response: {final_ai.content[:200]}...")

    return {"response": final_ai.content}


# Export everything needed
__all__ = [
    'analytics_tools',
    'analytics_llm_node',
    'analytics_formatter_node',
    'ToolNode',
    'get_sales',
    'get_profit',
    'get_last_n_days_sales',
    'get_product_performance'
]