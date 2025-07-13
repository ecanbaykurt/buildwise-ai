import streamlit as st
import sys
import os

# Make sure your backend package is discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.agent_manager import AgentManager  # ✅ your orchestrator

# -------------------------------
# ✅ Initialize Orchestrator Agent
# -------------------------------
orchestrator = AgentManager()

# -------------------------------
# ✅ Streamlit Page Setup
# -------------------------------
st.set_page_config(page_title="🏢 Buildwise AI — Multi-Agent Chatbot")
st.title("🏢 Buildwise AI — Multi-Agent Lease Assistant")

# -------------------------------
# ✅ Session State to store chat
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------------------------------
# ✅ Get User Input
# -------------------------------
user_input = st.chat_input("Ask me anything about your lease, a property, or your renewal...")

# -------------------------------
# ✅ Process Input with Orchestrator
# -------------------------------
if user_input:
    # Save user input to history
    st.session_state.chat_history.append(("user", user_input))

    # Use the orchestrator to handle the flow
    response = orchestrator.handle_request(user_input)

    # Save agent response to history
    st.session_state.chat_history.append(("agent", response))

# -------------------------------
# ✅ Render Chat History
# -------------------------------
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(msg)
