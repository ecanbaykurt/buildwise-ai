# streamlit_app.py

import streamlit as st
import requests

st.title("📚 Buildwise AI — Multi-Agent Lease Assistant")

st.header("Upload files")
uploaded_files = st.file_uploader(
    "Upload multiple files",
    type=['pdf', 'docx', 'csv', 'xlsx'],
    accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files:
        files = {"files": (file.name, file.getvalue())}
        res = requests.post("http://localhost:8000/upload_docs", files=files)
        st.write(res.json())

st.header("Ask a question")
user_input = st.text_input("Your question:")

if st.button("Ask"):
    res = requests.post("http://localhost:8000/chat", json={"message": user_input})
    st.write(res.json()["answer"])
