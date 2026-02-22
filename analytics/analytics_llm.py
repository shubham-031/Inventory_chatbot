import os
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
from models.state_models import InventoryState
from .analytics_tools import analytics_tools
from typing import Dict


# ✅ SAFE WORKING MODEL + API KEY
analytics_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    api_key=os.getenv("GEMINI_API_KEY")
).bind_tools(analytics_tools)

tool_node = ToolNode(analytics_tools)


def analytics_llm_node(state: InventoryState) -> Dict:
    """Node that lets Gemini decide which analytics tool to call"""

    user_query = state["user_query"]
    owner_id = state["owner_id"]

    system_prompt = (
        "You are an analytics assistant for a small grocery shop. "
        "You have access to tools that can fetch analytics from a MongoDB database. "
        "Always include the 'owner_id' argument when calling any tool."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Owner id: {owner_id}\nUser question: {user_query}"),
    ]

    ai_msg: AIMessage = analytics_llm.invoke(messages)
    return {"messages": [ai_msg]}


def analytics_formatter_node(state: InventoryState) -> Dict:
    """Format the analytics result into natural language"""

    user_query = state["user_query"]
    messages = state["messages"]

    tool_output_text = None
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "tool":
            tool_output_text = msg.content
            break

    if tool_output_text is None:
        tool_output_text = "{}"

    # ✅ Correct model here too
    analytics_formatter_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    system_prompt = (
        "You are a grocery shop analytics assistant. "
        "Explain the answer in 1-3 clear sentences. "
        "Do NOT call any tools. Do NOT invent numbers."
    )

    llm_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User question:\n{user_query}\n\nAnalytics JSON result:\n{tool_output_text}"),
    ]

    final_ai = analytics_formatter_llm.invoke(llm_messages)
    return {"response": final_ai.content}


def has_tool_calls(state: InventoryState) -> str:
    """Check if there are tool calls"""
    msgs = state["messages"]
    if not msgs:
        return "end"
    last = msgs[-1]
    tool_calls = getattr(last, "tool_calls", None)
    if tool_calls:
        return "tools"
    return "end"