import streamlit as st
import sys
import os

# Make sure backend is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.agent_manager import AgentManager  # ✅ import once

# ✅ Use one name consistently
manager = AgentManager()  # your orchestrator instance

# Page setup
st.set_page_config(page_title="🏢 Buildwise AI — Multi-Agent Chatbot")
st.title("🏢 Buildwise AI — Multi-Agent Lease Assistant")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Get input
user_input = st.chat_input("Ask me anything about your lease, a property, or your renewal...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))

    # ✅ Correct object name: manager not orchestrator
    response = manager.handle_request(user_input)

    st.session_state.chat_history.append(("agent", response))

# Render history
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(msg)
