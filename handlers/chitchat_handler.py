import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from models.state_models import InventoryState

# Load environment variables
load_dotenv()

# ✅ Correct model + API key
model = GoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3
)


def chitchat_node(state: InventoryState) -> InventoryState:
    """Handle chitchat and greetings"""

    last_summary = state.get("response", "")
    user_msg = state.get("user_query", "")
    db_results = state.get("db_results", "")

    CHITCHAT_PROMPT = ChatPromptTemplate.from_messages([
        (
            "system",
            (
                "You are a friendly inventory chatbot for a small grocery shop. "
                "You mainly do:\n"
                "1) Greetings (hi, hello, etc.).\n"
                "2) Simple follow-up questions based on the previous answer.\n\n"
                "If the user just greets, respond with a short greeting and ask how you can "
                "help with inventory, bills, suppliers, or analytics.\n"
                "If the user asks something about the previous answer, use ONLY the previous "
                "answer and database results given below as context. Do not invent new data.\n"
                "If you cannot answer, ask the user to rephrase or ask a data-related question."
            ),
        ),
        (
            "human",
            (
                "Previous answer (if any):\n{previous_answer}\n\n"
                "User message:\n{user_message}\n\n"
                "Database results (JSON):\n{db_results}"
            ),
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

    except Exception:
        return {"response": "Hi! 👋 How can I help you with your inventory today?"}