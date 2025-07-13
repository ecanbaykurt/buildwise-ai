from supabase import create_client, Client
import os

# Get your secrets securely (for local dev or Streamlit Cloud)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_user(email, name, phone):
    return supabase.table("users").insert({
        "email": email,
        "name": name,
        "phone": phone
    }).execute()

def get_user(email):
    # ✅ Use maybe_single so you don't get an APIError if user doesn't exist yet
    return supabase.table("users").select("*").eq("email", email).maybe_single().execute()

def create_conversation(user_id):
    return supabase.table("conversations").insert({
        "user_id": user_id
    }).execute()

def get_conversations(user_id):
    return supabase.table("conversations").select("*").eq("user_id", user_id).execute()

def add_message(conversation_id, sender, message_text):
    return supabase.table("chat_messages").insert({
        "conversation_id": conversation_id,
        "sender": sender,
        "message_text": message_text
    }).execute()

def get_messages(conversation_id):
    return supabase.table("chat_messages").select("*").eq("conversation_id", conversation_id).order("timestamp").execute()
