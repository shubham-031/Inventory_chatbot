import os
from dotenv import load_dotenv
from typing import Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
from models.state_models import InventoryState
from .analytics_tools import analytics_tools

load_dotenv()

# ✅ Safe LLM with single API key
analytics_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1,
    api_key=os.getenv("GEMINI_API_KEY")
).bind_tools(analytics_tools)

tool_node = ToolNode(analytics_tools)


def analytics_llm_node(state: InventoryState) -> Dict:
    """LLM decides whether to call analytics tools"""

    user_query = state.get("user_query")
    owner_id = state.get("owner_id")

    system_prompt = (
        "You are a grocery shop analytics assistant. "
        "You have access to analytics tools. "
        "Always include owner_id when calling tools."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Owner id: {owner_id}\nUser question: {user_query}"),
    ]

    ai_msg: AIMessage = analytics_llm.invoke(messages)

    # ✅ Append instead of overwrite
    return {
        "messages": state.get("messages", []) + [ai_msg]
    }


def analytics_formatter_node(state: InventoryState) -> Dict:
    """Format tool output into natural language"""

    user_query = state.get("user_query")
    messages = state.get("messages", [])

    tool_output_text = "{}"

    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type == "tool":
            tool_output_text = msg.content
            break

    formatter_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        api_key=os.getenv("GEMINI_API_KEY")
    )

    system_prompt = (
        "You are a grocery analytics assistant. "
        "Explain results clearly in 1-3 sentences. "
        "Do NOT invent numbers."
    )

    llm_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"User question:\n{user_query}\n\nAnalytics JSON result:\n{tool_output_text}"
        ),
    ]

    final_ai = formatter_llm.invoke(llm_messages)

    return {
        **state,
        "response": final_ai.content
    }


def has_tool_calls(state: InventoryState) -> str:
    msgs = state.get("messages", [])
    if not msgs:
        return "end"

    last = msgs[-1]
    tool_calls = getattr(last, "tool_calls", None)

    if tool_calls:
        return "tools"
    return "end"