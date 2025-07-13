import streamlit as st
from backend.db.supabase_client import (
    create_user, get_user, create_conversation, add_message, get_messages
)
from openai import OpenAI

# Load secrets securely
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Setup OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="Buildwise AI — Multi-Agent Lease Assistant")

st.title("🏢 Buildwise AI — Multi-Agent Lease Assistant")

# --- 1️⃣ Onboarding ---
email = st.text_input("Your Email")
phone = st.text_input("Your Phone")

if "user_id" not in st.session_state and st.button("Start Chat") and email:
    user = get_user(email).data
    if not user:
        create_user(email=email, name="New User", phone=phone)
        user = get_user(email).data
    st.session_state["user_id"] = user["id"]
    convo = create_conversation(user["id"]).data[0]
    st.session_state["conversation_id"] = convo["id"]

# --- 2️⃣ Show chat if onboarding complete ---
if "conversation_id" in st.session_state:
    st.success(f"Welcome back, {email}!")
    messages = get_messages(st.session_state["conversation_id"]).data

    for msg in messages:
        with st.chat_message(msg["sender"]):
            st.write(msg["message_text"])

    # New user input
    user_input = st.chat_input("Type your question...")
    if user_input:
        add_message(st.session_state["conversation_id"], "user", user_input)
        
        # --- Call OpenAI agent ---
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful leasing agent."},
                {"role": "user", "content": user_input}
            ]
        )
        agent_reply = response.choices[0].message.content

        add_message(st.session_state["conversation_id"], "agent", agent_reply)

        with st.chat_message("agent"):
            st.write(agent_reply)
