import streamlit as st
import sys
import os

# Ensure backend package is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.supabase_client import (
    create_user, get_user, create_conversation, add_message, get_messages
)
from openai import OpenAI

# Load secrets securely
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Setup OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Page setup
st.set_page_config(page_title="Buildwise AI — Multi-Agent Lease Assistant")
st.title("🏢 Buildwise AI — Multi-Agent Lease Assistant")

# --- ✅ User Onboarding ---
# ✅ Normalize user input
email = st.text_input("Your Email").strip().lower()   # <-- FIXED: strip and lowercase!
phone = st.text_input("Your Phone")

if "user_id" not in st.session_state:
    if st.button("Start Chat"):
        if email:
            # ✅ Debug: See what email you’re actually querying
            st.write(f"Checking user with email: '{email}'")

            user_response = get_user(email)
            user = user_response.data

            if not user:
                create_user(email=email, name="New User", phone=phone)
                user = get_user(email).data

            if user:
                st.session_state["user_id"] = user["id"]
                convo_response = create_conversation(user["id"])
                convo = convo_response.data[0]
                st.session_state["conversation_id"] = convo["id"]
            else:
                st.error("Something went wrong creating your user.")
        else:
            st.error("Please enter your email.")

# --- ✅ Chat Interaction ---
if "conversation_id" in st.session_state:
    st.success(f"Welcome back, {email}!")

    # Display existing messages
    messages = get_messages(st.session_state["conversation_id"]).data
    for msg in messages:
        with st.chat_message(msg["sender"]):
            st.write(msg["message_text"])

    # New user input
    user_input = st.chat_input("Type your question...")
    if user_input:
        add_message(st.session_state["conversation_id"], "user", user_input)

        # Call OpenAI agent
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful leasing agent."},
                {"role": "user", "content": user_input}
            ]
        )
        agent_reply = response.choices[0].message.content

        add_message(st.session_state["conversation_id"], "agent", agent_reply)

        # Display agent response
        with st.chat_message("agent"):
            st.write(agent_reply)
