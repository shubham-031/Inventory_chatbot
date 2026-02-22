"""
Smart Inventory AI - Modern Chat Interface
Beautiful, clean, and fully functional
"""
import streamlit as st
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

load_dotenv() 


# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Imports
try:
    from chatbot_runner import workflow, InventoryState
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.stop()

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Smart Inventory AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== MODERN CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main background */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #2d3748;
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #fff;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Input styling */
    .stTextInput > label {
        color: #a0aec0 !important;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .stTextInput input {
        background: #1a202c !important;
        border: 2px solid #4a5568 !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
    }
    
    .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Quick action buttons */
    [data-testid="stSidebar"] .stButton > button {
        background: #4a5568;
        box-shadow: none;
        font-size: 0.9rem;
        padding: 0.65rem 1rem;
        text-align: left;
        justify-content: flex-start;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #667eea;
    }
    
    /* Header */
    .main-header {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 2rem;
        text-align: center;
        color: white;
        border-radius: 20px;
        margin: 1rem auto 2rem;
        max-width: 1400px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(to right, #fff, #e0e7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin: 0 auto 2rem;
        max-width: 1400px;
        min-height: 550px;
        max-height: 550px;
        overflow-y: auto;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    }
    
    /* Custom scrollbar */
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 10px;
    }
    
    /* Messages */
    .message {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .user-message {
        flex-direction: row-reverse;
    }
    
    .user-message .message-avatar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .assistant-message .message-avatar {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .message-content {
        max-width: 70%;
        padding: 1rem 1.25rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        line-height: 1.6;
    }
    
    .user-message .message-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .assistant-message .message-content {
        background: #f7fafc;
        color: #2d3748;
        border-bottom-left-radius: 4px;
    }
    
    .message-time {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 0.5rem;
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #a0aec0;
    }
    
    .empty-state h3 {
        color: #4a5568;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Info box */
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.25rem;
        border-radius: 12px;
        margin-top: 1.5rem;
        font-size: 0.9rem;
        line-height: 1.8;
    }
    
    .info-box strong {
        font-weight: 600;
    }
    
    /* Feature cards */
    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
    }
    
    .feature-card h3 {
        color: #667eea;
        font-size: 1.3rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .feature-card ul {
        list-style: none;
        padding: 0;
    }
    
    .feature-card li {
        padding: 0.5rem 0;
        color: #4a5568;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .feature-card li:before {
        content: "✓";
        color: #667eea;
        font-weight: bold;
        font-size: 1.2rem;
    }
    
    /* Input area */
    .chat-input-container {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 0 auto;
        max-width: 1400px;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Welcome section */
    .welcome {
        text-align: center;
        padding: 3rem 2rem;
        color: white;
    }
    
    .welcome h2 {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    
    .welcome p {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: #48bb78 !important;
        color: white !important;
        border-radius: 12px !important;
    }
    
    .stError {
        background: #f56565 !important;
        color: white !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "owner_id" not in st.session_state:
    st.session_state.owner_id = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "processing" not in st.session_state:
    st.session_state.processing = False

# ==================== HELPER FUNCTION ====================
def process_message(user_input: str):
    """Process user message through workflow"""
    if not user_input or not user_input.strip():
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
        # Create state
        state = {
            "owner_id": st.session_state.owner_id,
            "user_query": user_input.strip(),
            "messages": []
        }
        
        config = {
            "configurable": {
                "thread_id": st.session_state.session_id
            }
        }
        
        # Run workflow
        result = workflow.invoke(input=state, config=config)
        
        # Get response
        response = result.get("response", "I couldn't process that request. Please try again.")
        
        # Add bot message
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
    except Exception as e:
        # Add error message
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ Sorry, I encountered an error: {str(e)[:100]}",
            "timestamp": datetime.now().strftime("%H:%M")
        })
    
    finally:
        st.session_state.processing = False
    
    st.rerun()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🔐 Login")
    
    email = st.text_input(
        "Your Email",
        value=st.session_state.owner_id or "",
        placeholder="jadhavshubham9718@gmail.com",
        key="email_input"
    )
    
    if st.button("🚀 Connect"):
        if email and "@" in email:
            st.session_state.owner_id = email
            st.session_state.session_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.session_state.messages = []
            st.success("✅ Connected!")
            st.rerun()
        else:
            st.error("⚠️ Please enter a valid email")
    
    if st.session_state.owner_id:
        st.markdown("---")
        st.markdown("## ⚡ Quick Actions")
        
        quick_actions = {
            "📦 All Products": "Show me all products",
            "💰 Today's Sales": "What are today's sales?",
            "📊 Today's Profit": "What's today's profit?",
            "📈 Top Products": "Show top selling products",
            "⚠️ Low Stock": "Which products are low in stock?",
            "🧾 Today's Bills": "Show today's bills",
            "🏭 Suppliers": "Show all suppliers",
        }
        
        for label, query in quick_actions.items():
            if st.button(label, key=f"qa_{label}"):
                process_message(query)
        
        st.markdown("---")
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown(f"""
        <strong>👤 User:</strong> {st.session_state.owner_id}<br>
        <strong>💬 Messages:</strong> {len(st.session_state.messages)}<br>
        <strong>🕐 Session:</strong> {st.session_state.session_id[-6:] if st.session_state.session_id else 'N/A'}
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

# ==================== MAIN CONTENT ====================
st.markdown("""
<div class="main-header">
    <h1>🤖 Smart Inventory AI</h1>
    <p>Your Intelligent Inventory Management Assistant</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.owner_id:
    # ==================== WELCOME SCREEN ====================
    st.markdown("""
    <div class="welcome">
        <h2>👋 Welcome to Smart Inventory AI</h2>
        <p>Manage your inventory with the power of artificial intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📦 Product Management</h3>
            <ul>
                <li>Real-time stock tracking</li>
                <li>Expiry date monitoring</li>
                <li>Category management</li>
                <li>Smart stock alerts</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>💰 Sales Analytics</h3>
            <ul>
                <li>Daily sales reports</li>
                <li>Profit calculations</li>
                <li>Trend analysis</li>
                <li>Customer insights</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Smart Reports</h3>
            <ul>
                <li>Top selling items</li>
                <li>Bill tracking</li>
                <li>Supplier management</li>  
                <li>Custom analytics</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("👈 Please login using the sidebar to start chatting!")

else:
    # ==================== CHAT INTERFACE ====================
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <h3>💬 Start a Conversation</h3>
            <p>Type a message below or use Quick Actions from the sidebar</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display messages
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="message user-message">
                    <div class="message-content">
                        {msg["content"]}
                        <div class="message-time">{msg["timestamp"]}</div>
                    </div>
                    <div class="message-avatar">👤</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message assistant-message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        {msg["content"]}
                        <div class="message-time">{msg["timestamp"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ==================== INPUT AREA ====================
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
    
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="Ask about products, sales, inventory...",
                label_visibility="collapsed",
                disabled=st.session_state.processing
            )
        
        with col2:
            send_button = st.form_submit_button(
                "📤 Send",
                use_container_width=True,
                disabled=st.session_state.processing
            )
        
        if send_button and user_input:
            process_message(user_input)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== FOOTER ====================
st.markdown("""
<div style="text-align: center; padding: 2rem; color: white; opacity: 0.8;">
    <p>Powered by Google Gemini AI • Made with ❤️ for Smart Businesses</p>
</div>
""", unsafe_allow_html=True)