from supabase import create_client, Client
import os

"""
This module connects your app to Supabase.
Use these helper functions for all CRUD operations.
"""

# Load your Supabase secrets (works locally with .env or in Streamlit Cloud with st.secrets)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def create_user(email, name, phone):
    """Insert a new user into the 'users' table."""
    return supabase.table("users").insert({
        "email": email,
        "name": name,
        "phone": phone
    }).execute()


def get_user(email):
    """
    Get exactly one user by email.
    ✅ Uses maybe_single() so no rows returns None instead of throwing an error.
    """
    return (
        supabase
        .table("users")
        .select("*")
        .eq("email", email)
        .maybe_single()
        .execute()
    )


def create_conversation(user_id):
    """Start a new conversation for a given user_id."""
    return supabase.table("conversations").insert({
        "user_id": user_id
    }).execute()


def get_conversations(user_id):
    """Get all conversations for a given user_id."""
    return supabase.table("conversations").select("*").eq("user_id", user_id).execute()


def add_message(conversation_id, sender, message_text):
    """Add a message to a conversation."""
    return supabase.table("chat_messages").insert({
        "conversation_id": conversation_id,
        "sender": sender,
        "message_text": message_text
    }).execute()


def get_messages(conversation_id):
    """Get all messages for a conversation, ordered by timestamp."""
    return (
        supabase
        .table("chat_messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("timestamp")
        .execute()
    )
