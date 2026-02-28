"""
Smart Inventory AI - Modern Chat Interface
Fully Corrected Version
"""

import streamlit as st
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# ==================== LOAD ENV ====================
load_dotenv()

# ==================== PATH SETUP ====================
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ==================== IMPORT WORKFLOW ====================
try:
    from chatbot_runner import workflow
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.stop()

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Smart Inventory AI",
    page_icon="🤖",
    layout="wide"
)

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "owner_id" not in st.session_state:
    st.session_state.owner_id = None

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "processing" not in st.session_state:
    st.session_state.processing = False


# ==================== PROCESS MESSAGE FUNCTION ====================
def process_message(user_input: str):
    if not user_input.strip():
        return

    if st.session_state.processing:
        return

    st.session_state.processing = True

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input.strip(),
        "timestamp": datetime.now().strftime("%H:%M")
    })

    try:
        # ✅ COMPLETE STATE STRUCTURE
        state = {
            "owner_id": st.session_state.owner_id,
            "user_query": user_input.strip(),
            "mongo_query": None,
            "intent": None,
            "collection": None,
            "db_results": None,
            "response": None,
            "messages": []
        }

        config = {
            "configurable": {
                "thread_id": st.session_state.session_id
            }
        }

        # ✅ CORRECT LANGGRAPH INVOCATION
        result = workflow.invoke(state, config=config)

        # ✅ SAFE RESPONSE EXTRACTION
        response = result.get("response")

        if not response:
            response = "⚠️ No response generated. Please check workflow nodes."

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M")
        })

    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ Error: {str(e)}",
            "timestamp": datetime.now().strftime("%H:%M")
        })

    finally:
        st.session_state.processing = False

    st.rerun()


# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("🔐 Login")

    email = st.text_input(
        "Your Email",
        value=st.session_state.owner_id or "",
        placeholder="example@gmail.com"
    )

    if st.button("🚀 Connect"):
        if email and "@" in email:
            st.session_state.owner_id = email
            st.session_state.session_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.session_state.messages = []
            st.success("✅ Connected!")
            st.rerun()
        else:
            st.error("⚠️ Enter valid email")

    if st.session_state.owner_id:
        st.markdown("---")
        st.write(f"👤 {st.session_state.owner_id}")
        st.write(f"💬 Messages: {len(st.session_state.messages)}")

        if st.button("🗑 Clear Chat"):
            st.session_state.messages = []
            st.rerun()


# ==================== MAIN HEADER ====================
st.title("🤖 Smart Inventory AI")
st.caption("Your Intelligent Inventory Assistant")

# ==================== CHAT AREA ====================
if not st.session_state.owner_id:
    st.info("👈 Please login from sidebar to start chatting.")
else:

    # Display chat messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

    # Input box
    user_input = st.chat_input("Ask about products, sales, suppliers...")

    if user_input:
        process_message(user_input)