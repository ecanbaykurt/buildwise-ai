import streamlit as st
import sys
import os

# Add backend to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.orchestrator import Orchestrator

orchestrator = Orchestrator()

st.set_page_config(page_title="🏢 Buildwise AI — Multi-Agent Lease Demo")
st.title("🏢 Buildwise AI — Multi-Agent Lease Demo")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Show conversation history
for role, msg in st.session_state["chat_history"]:
    with st.chat_message(role):
        st.write(msg)

# User input
user_input = st.chat_input("Ask me to find you a unit!")

if user_input:
    st.session_state["chat_history"].append(("user", user_input))
    response = orchestrator.handle_request(user_input)
    st.session_state["chat_history"].append(("assistant", response))

    with st.chat_message("assistant"):
        st.write(response)
