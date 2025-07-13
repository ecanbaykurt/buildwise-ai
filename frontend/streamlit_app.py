import streamlit as st
from backend.orchestrator import Orchestrator
from datetime import datetime
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Setup Orchestrator once
orchestrator = Orchestrator()

# --- Page configuration ---
st.set_page_config(
    page_title="OkadaAI - Commercial Real Estate Assistant",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS styling ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* Your custom styles here... (keep your same CSS from your file) */
</style>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if 'selected_agent' not in st.session_state:
    st.session_state.selected_agent = 'OKA'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- Header ---
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

# --- Agent selection ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    agent_options = {
        'OKA': 'Find & discover spaces',
        'ADA': 'Lease support & guidance'
    }
    selected_agent = st.selectbox(
        "Choose your AI assistant:",
        options=list(agent_options.keys()),
        index=0 if st.session_state.selected_agent == 'OKA' else 1,
        format_func=lambda x: f"{x} - {agent_options[x]}"
    )
    st.session_state.selected_agent = selected_agent

# --- Welcome ---
st.markdown("""
<div class="welcome-section">
    <h2 class="welcome-title">Finding your next great space in NYC, effortlessly</h2>
    <p class="welcome-subtitle">Discover premium commercial properties tailored to your business needs</p>
</div>
""", unsafe_allow_html=True)

# --- Search / Query Input ---
st.markdown('<div class="search-section">', unsafe_allow_html=True)

if selected_agent == 'OKA':
    st.markdown("### 🔍 Hi! I'm OKA. What space are you looking for?")
    search_placeholder = "I want to find..."
    context_text = "I'll help you discover commercial spaces that match your needs, budget, and preferences. Tell me about your business and requirements!"
else:
    st.markdown("### 📋 Hi! I'm ADA. How can I help with your lease?")
    search_placeholder = "I need help with..."
    context_text = "I'm here to help you understand lease agreements, explain property details, and support you through the rental process. What questions do you have?"

search_query = st.text_input(
    "Search",
    placeholder=search_placeholder,
    label_visibility="collapsed"
)

st.markdown(f'<div class="agent-info">{context_text}</div>', unsafe_allow_html=True)

if search_query:
    with st.spinner(f"⏳ {selected_agent} is thinking..."):
        agent_response = orchestrator.handle_chat_request(search_query)
    st.success(f"✅ {selected_agent} response ready!")
    st.session_state.chat_history.append(
        {"role": "user", "content": search_query}
    )
    st.session_state.chat_history.append(
        {"role": "assistant", "content": agent_response}
    )
    st.markdown(f"""
    <div style="background: #f9f9f9; border-left: 4px solid #667eea; padding: 15px; border-radius: 10px; margin: 15px 0;">
        {agent_response}
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- Optional Chat Mode ---
if st.checkbox("Enable Chat Mode"):
    st.markdown("### Chat with " + selected_agent)
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input(f"Ask {selected_agent} anything..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner(f"⏳ {selected_agent} is preparing an answer..."):
            response = orchestrator.handle_chat_request(prompt)

        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)

# --- Sidebar Quick Actions (optional) ---
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
    st.markdown("### Agent Info")
    if selected_agent == 'OKA':
        st.info("🔍 **OKA**: Property discovery, needs assessment, and matching ideal spaces.")
    else:
        st.info("📋 **ADA**: Lease agreements, contract explanations, and tenant support.")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 20px;">
    🏢 OkadaAI — Your AI-powered commercial real estate experience
</div>
""", unsafe_allow_html=True)
