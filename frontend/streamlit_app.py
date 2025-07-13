import streamlit as st
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.agent_manager import AgentManager

# Init orchestrator
manager = AgentManager()

st.set_page_config(page_title="🏢 Buildwise AI — Multi-Agent Chatbot")
st.title("🏢 Buildwise AI — Multi-Agent Lease Assistant")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User input
user_input = st.chat_input("Ask me anything about your lease, a property, or your renewal...")

if user_input:
    # Show user message
    st.session_state.chat_history.append(("user", user_input))

    # 🔗 Use Agent Manager to handle flow
    response = manager.handle(user_input)

    st.session_state.chat_history.append(("agent", response))

# Show chat
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(msg)
