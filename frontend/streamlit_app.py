import sys
import os
import streamlit as st
import pandas as pd
from openai import OpenAI

# ✅ Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ Load your data safely
@st.cache_data(show_spinner=False)
def load_data():
    building_df = pd.read_csv("building_data.csv")
    unit_df = pd.read_csv("unit_data.csv")
    return building_df, unit_df

building_df, unit_df = load_data()

# ✅ Setup OpenAI client
client = OpenAI()

# ✅ System prompt for consistent role
SYSTEM_PROMPT = (
    "You are OkadaAI, an expert commercial real estate assistant. "
    "You help users find and lease NYC commercial spaces. "
    "Always reason step-by-step. Use the data if possible; "
    "if the info is not in the dataset, respond politely."
)

# --- ✅ Page config ---
st.set_page_config(
    page_title="OkadaAI - Commercial Real Estate Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ✅ Custom CSS ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- ✅ Session State ---
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = "OKA"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- ✅ Header ---
st.markdown("""
<div class="main-header">
  <div class="logo-section">
    <div class="logo-icon">O</div>
    <div>
      <h1 style="margin: 0; font-size: 2rem;">OkadaAI</h1>
      <p style="margin: 0; opacity: 0.8;">Commercial Real Estate Assistant</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# --- ✅ Agent Selection ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    agent_options = {
        "OKA": "Find & discover spaces",
        "ADA": "Lease support & guidance"
    }
    selected_agent = st.selectbox(
        "Choose your AI assistant:",
        options=list(agent_options.keys()),
        index=0 if st.session_state.selected_agent == "OKA" else 1,
        format_func=lambda x: f"{x} - {agent_options[x]}"
    )
    st.session_state.selected_agent = selected_agent

# --- ✅ Welcome Section ---
st.markdown("""
<div class="welcome-section">
  <h2 class="welcome-title">Finding your next great space in NYC, effortlessly</h2>
  <p class="welcome-subtitle">Discover premium commercial properties tailored to your business needs</p>
</div>
""", unsafe_allow_html=True)

# --- ✅ Query Section ---
st.markdown('<div class="search-section">', unsafe_allow_html=True)

if selected_agent == "OKA":
    st.markdown("### 🔍 Hi! I'm OKA. What space are you looking for?")
    search_placeholder = "I want to find..."
    context_text = "I'll help you discover commercial spaces that match your needs, budget, and preferences."
    df_used = building_df
else:
    st.markdown("### 📋 Hi! I'm ADA. How can I help with your lease?")
    search_placeholder = "I need help with..."
    context_text = "I'm here to help you understand lease agreements, explain terms, and support you through the rental process."
    df_used = unit_df

search_query = st.text_input(
    "Search",
    placeholder=search_placeholder,
    label_visibility="collapsed"
)

st.markdown(f'<div class="agent-info">{context_text}</div>', unsafe_allow_html=True)

# --- ✅ Process Query ---
def ask_openai_with_data(user_query, df):
    sample_data = df.head(3).to_string()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here is some example data:\n{sample_data}\n\n"
                       f"My question: {user_query}"
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return response.choices[0].message.content

# --- ✅ Safe response ---
if search_query:
    with st.spinner(f"⏳ {selected_agent} is processing your request..."):
        try:
            agent_response = ask_openai_with_data(search_query, df_used)
            st.session_state.chat_history.append({"role": "user", "content": search_query})
            st.session_state.chat_history.append({"role": "assistant", "content": agent_response})
            st.success(f"✅ {selected_agent} response ready!")
        except Exception as e:
            agent_response = f"⚠️ Oops! Something went wrong: {e}"
            st.session_state.chat_history.append({"role": "assistant", "content": agent_response})
            st.error(agent_response)

    st.markdown(f"""
    <div style="background: #f9f9f9; border-left: 4px solid #667eea; padding: 15px; border-radius: 10px; margin: 15px 0;">
      {agent_response}
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- ✅ Optional Chat Mode ---
if st.checkbox("Enable Chat Mode"):
    st.markdown(f"### Chat with {selected_agent}")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input(f"Ask {selected_agent} anything..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner(f"⏳ {selected_agent} is preparing an answer..."):
            try:
                response = ask_openai_with_data(prompt, df_used)
            except Exception as e:
                response = f"⚠️ Error: {e}"

        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)

# --- ✅ Sidebar Actions ---
with st.sidebar:
    st.markdown("### Quick Actions")
    if st.button("💼 Office Space Search"):
        st.session_state.search_query = "Looking for office space"
        st.rerun()
    if st.button("🏪 Retail Location"):
        st.session_state.search_query = "Need retail location"
        st.rerun()
    if st.button("💰 Budget Info"):
        st.session_state.search_query = "Budget under $10k"
        st.rerun()
    if st.button("📅 Schedule Tour"):
        st.session_state.search_query = "Schedule a tour"
        st.rerun()
    st.markdown("---")
    if selected_agent == "OKA":
        st.info("🔍 **OKA**: Property discovery, matching, and needs assessment.")
    else:
        st.info("📋 **ADA**: Lease guidance, contract clarifications, and tenant support.")

# --- ✅ Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 20px;">
🏢 OkadaAI — Your AI-powered commercial real estate experience
</div>
""", unsafe_allow_html=True)
