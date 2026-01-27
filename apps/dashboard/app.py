import json
import requests
import streamlit as st

st.set_page_config(page_title="AI Customer Agent Dashboard", layout="wide")

st.title("AI Customer Agent (Grounded)")
st.caption("Answers strictly from the Knowledge Base. If not supported, it refuses.")

api_url = st.sidebar.text_input("API URL", value="http://127.0.0.1:8000")

col1, col2 = st.columns([2, 1])

with col1:
    q = st.text_input("Ask a question", placeholder="e.g., How do I schedule a DPS appointment?")
    if st.button("Send") and q.strip():
        try:
            r = requests.post(f"{api_url}/chat", json={"message": q}, timeout=60)
            r.raise_for_status()
            data = r.json()
            st.subheader("Answer")
            st.write(data.get("answer", ""))

            st.subheader("Sources")
            st.json(data.get("sources", []))
            st.caption(f"Refusal: {data.get('refusal')} | Best similarity: {data.get('best_similarity')}")
        except Exception as e:
            st.error(f"API error: {e}")

with col2:
    st.subheader("KB Operations")
    if st.button("Ingest / Rebuild Index"):
        try:
            r = requests.post(f"{api_url}/ingest", timeout=120)
            r.raise_for_status()
            st.success("Ingested KB")
            st.json(r.json())
        except Exception as e:
            st.error(f"Ingest error: {e}")
