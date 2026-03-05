from __future__ import annotations

import time
from typing import Any, Dict, List

import requests
import streamlit as st

st.set_page_config(
    page_title="Texas DPS Virtual Assistant",
    page_icon="*",
    layout="centered",
    initial_sidebar_state="collapsed",
)

API_DEFAULT = "http://127.0.0.1:8000"

SUGGESTED_PROMPTS: List[Dict[str, str]] = [
    {"label": "Driver License", "prompt": "How do I apply for a Texas driver license?"},
    {"label": "State ID Card", "prompt": "What documents do I need for a Texas ID card?"},
    {"label": "Book Appointment", "prompt": "I want to book a DL appointment"},
    {"label": "Renew Online", "prompt": "Can I renew my driver license online?"},
    {"label": "Commercial DL", "prompt": "What are the requirements for a CDL?"},
    {"label": "FAQ", "prompt": "What are the most common DL questions?"},
]

SERVICE_LINKS: List[Dict[str, str]] = [
    {"title": "Schedule Appointment", "url": "https://www.dps.texas.gov/section/service/new-appointment-scheduling-system"},
    {"title": "Online Services", "url": "https://www.dps.texas.gov/section/driver-license/online-services"},
    {"title": "DL Requirements", "url": "https://www.dps.texas.gov/section/driver-license/requirements"},
    {"title": "ID Cards", "url": "https://www.dps.texas.gov/section/driver-license/how-apply-texas-identification-card"},
    {"title": "CDL Info", "url": "https://www.dps.texas.gov/section/commercial-driver-license"},
    {"title": "FAQ", "url": "https://www.dps.texas.gov/section/driver-license/how-can-we-help"},
]

_CSS = """
<style>
:root {
    --dps-navy: #002868;
    --dps-navy-dark: #001845;
    --dps-light: #f5f7fa;
    --radius: 1rem;
    --shadow-sm: 0 1px 3px rgba(0,0,0,.08);
    --shadow-md: 0 4px 12px rgba(0,0,0,.10);
}
html, body, [data-testid="stAppViewContainer"] {
    background: var(--dps-light) !important;
}
[data-testid="stSidebar"] {
    background: var(--dps-navy-dark) !important;
}
[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select {
    background: rgba(255,255,255,.1) !important;
    border: 1px solid rgba(255,255,255,.2) !important;
    color: #fff !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }

.dps-banner {
    background: linear-gradient(135deg, var(--dps-navy) 0%, var(--dps-navy-dark) 100%);
    color: #fff;
    padding: 1.1rem 1.6rem;
    border-radius: var(--radius);
    text-align: center;
    margin-bottom: 1.2rem;
    box-shadow: var(--shadow-md);
}
.dps-banner .title {
    font-size: 1.25rem;
    font-weight: 700;
}
.dps-banner .subtitle {
    font-size: .82rem;
    opacity: .85;
    margin-top: 2px;
}

.welcome-hero {
    text-align: center;
    padding: 2.5rem 1rem 1rem;
}
.welcome-hero h2 {
    font-size: 1.6rem;
    color: var(--dps-navy);
    margin-bottom: .3rem;
}
.welcome-hero p {
    color: #555;
    font-size: .95rem;
    max-width: 520px;
    margin: 0 auto;
}

.source-card {
    background: #f0f4ff;
    border-left: 3px solid var(--dps-navy);
    border-radius: .4rem;
    padding: .5rem .8rem;
    margin-top: .45rem;
    font-size: .78rem;
    color: #333;
}
.source-card strong { color: var(--dps-navy); }

.typing-dots span {
    display: inline-block;
    width: 7px;
    height: 7px;
    margin: 0 2px;
    background: var(--dps-navy);
    border-radius: 50%;
    animation: bounce .9s infinite;
}
.typing-dots span:nth-child(2) { animation-delay: .15s; }
.typing-dots span:nth-child(3) { animation-delay: .3s; }
@keyframes bounce {
    0%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-6px); }
}

.link-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: .55rem;
    margin-top: .8rem;
}
.link-card {
    background: #fff;
    border: 1px solid #e0e4ea;
    border-radius: .6rem;
    padding: .65rem .85rem;
    font-size: .82rem;
    font-weight: 600;
    color: var(--dps-navy);
    text-decoration: none !important;
    transition: all .15s;
    box-shadow: var(--shadow-sm);
}
.link-card:hover {
    border-color: var(--dps-navy);
    background: #eff3fa;
}

.dps-footer {
    text-align: center;
    font-size: .7rem;
    color: #999;
    padding: 1.5rem 0 .5rem;
}

[data-testid="stChatInput"] {
    max-width: 740px !important;
    margin: 0 auto !important;
}
[data-testid="stChatInput"] textarea {
    border-radius: 1.2rem !important;
    border: 1.5px solid #d0d5dd !important;
    padding: .8rem 1.2rem !important;
    box-shadow: var(--shadow-sm) !important;
    font-size: .92rem !important;
    color: #000 !important;
    -webkit-text-fill-color: #000 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #444 !important;
    opacity: 1 !important;
}
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: .2rem 0 !important;
    max-width: 740px;
    margin: 0 auto;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
    color: #000 !important;
}

div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background: #fff !important;
    border: 1.5px solid #e0e4ea !important;
    border-radius: .8rem !important;
    padding: .65rem 1rem !important;
    font-size: .88rem !important;
    color: #333 !important;
    transition: all .18s ease !important;
    box-shadow: var(--shadow-sm) !important;
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
    border-color: var(--dps-navy) !important;
    background: #eff3fa !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def _init_state() -> None:
    st.session_state.setdefault("session_id", "")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("api_url", API_DEFAULT)
    st.session_state.setdefault("pending_prompt", None)
    st.session_state.setdefault("user_name", "")
    st.session_state.setdefault("rag_debug_query", "")
    st.session_state.setdefault("rag_hits", [])


def _call_chat(api_url: str, session_id: str, message: str) -> Dict[str, Any]:
    payload = {"session_id": session_id or None, "message": message}
    r = requests.post(f"{api_url}/chat", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def _call_retrieve(api_url: str, message: str) -> Dict[str, Any]:
    payload = {"session_id": None, "message": message}
    r = requests.post(f"{api_url}/retrieve", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def _call_history(api_url: str, session_id: str, limit: int = 50) -> Dict[str, Any]:
    r = requests.get(f"{api_url}/history/{session_id}", params={"limit": limit}, timeout=30)
    r.raise_for_status()
    return r.json()


def _render_banner() -> None:
    st.markdown(
        """
        <div class="dps-banner">
            <div class="title">Texas DPS Virtual Assistant</div>
            <div class="subtitle">Driver License and ID Card Services</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_welcome() -> None:
    st.markdown(
        """
        <div class="welcome-hero">
            <h2>How can I help you today?</h2>
            <p>Ask about driver licenses, ID cards, appointments, renewals, and requirements.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    for idx, prompt in enumerate(SUGGESTED_PROMPTS):
        with cols[idx % 3]:
            if st.button(prompt["label"], key=f"sp_{idx}", use_container_width=True):
                st.session_state["pending_prompt"] = prompt["prompt"]
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### Popular DPS Links")
    link_html = '<div class="link-grid">'
    for item in SERVICE_LINKS:
        link_html += f'<a href="{item["url"]}" target="_blank" class="link-card">{item["title"]}</a>'
    link_html += "</div>"
    st.markdown(link_html, unsafe_allow_html=True)


def _render_assistant_meta(meta: Dict[str, Any]) -> None:
    parts: List[str] = []
    if meta.get("intent"):
        parts.append(f"Intent: {meta['intent']}")
    if meta.get("best_similarity") is not None:
        parts.append(f"Confidence: {meta['best_similarity']:.2%}")
    timings = meta.get("timings_ms") or {}
    if timings:
        total_ms = sum(float(v or 0) for v in timings.values())
        parts.append(f"Latency: {int(total_ms)} ms")
    if parts:
        st.caption(" | ".join(parts))

    sources = meta.get("sources") or []
    if sources:
        with st.expander("Sources", expanded=False):
            for src in sources:
                title = src.get("title", "Source")
                url = src.get("source_url", "")
                sim = src.get("similarity", 0)
                link_part = f' - <a href="{url}" target="_blank">link</a>' if url else ""
                st.markdown(
                    f'<div class="source-card"><strong>{title}</strong>{link_part}'
                    f"<br>Similarity: {sim:.4f}</div>",
                    unsafe_allow_html=True,
                )


def _render_message(msg: Dict[str, Any]) -> None:
    role = msg["role"]
    avatar = "🤖" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])
        if role == "assistant":
            _render_assistant_meta(msg.get("meta") or {})


def _render_chat_history() -> None:
    for msg in st.session_state["messages"]:
        _render_message(msg)


def _history_to_messages(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    for event in events:
        role = event.get("role")
        if role not in {"user", "assistant"}:
            continue
        item: Dict[str, Any] = {"role": role, "content": event.get("content", "")}
        if role == "assistant":
            item["meta"] = {
                "intent": event.get("intent"),
                "refusal": event.get("refusal"),
                "best_similarity": event.get("best_similarity"),
                "sources": event.get("sources", []),
                "timings_ms": event.get("timings_ms", {}),
            }
        messages.append(item)
    return messages


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Settings")
        st.session_state["api_url"] = st.text_input("API Endpoint", value=st.session_state["api_url"])

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Health", use_container_width=True):
                try:
                    r = requests.get(f"{st.session_state['api_url']}/health", timeout=10)
                    r.raise_for_status()
                    st.success("API is reachable")
                except Exception as exc:
                    st.error(f"Health check failed: {exc}")
        with c2:
            if st.button("Reload History", use_container_width=True):
                session_id = st.session_state.get("session_id", "")
                if not session_id:
                    st.info("No active session yet.")
                else:
                    try:
                        data = _call_history(st.session_state["api_url"], session_id=session_id, limit=100)
                        events = data.get("events", [])
                        st.session_state["messages"] = _history_to_messages(events)
                        st.success(f"Loaded {len(events)} events")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"History error: {exc}")

        st.divider()
        st.markdown("### Session")
        if st.session_state["session_id"]:
            st.code(st.session_state["session_id"], language=None)
        else:
            st.caption("No active session")

        if st.session_state.get("user_name"):
            st.markdown(f"**User:** {st.session_state['user_name']}")

        if st.button("New Conversation", use_container_width=True):
            st.session_state["session_id"] = ""
            st.session_state["messages"] = []
            st.session_state["user_name"] = ""
            st.session_state["pending_prompt"] = None
            st.rerun()

        st.divider()
        st.markdown("### Analytics")
        if st.button("Refresh Stats", use_container_width=True):
            try:
                r = requests.get(f"{st.session_state['api_url']}/stats", timeout=10)
                r.raise_for_status()
                st.session_state["_stats"] = r.json()
            except Exception as exc:
                st.error(f"Stats error: {exc}")
        stats = st.session_state.get("_stats")
        if stats:
            c1, c2 = st.columns(2)
            c1.metric("Sessions", stats.get("total_sessions", 0))
            c2.metric("Messages", stats.get("total_messages", 0))
            c3, c4 = st.columns(2)
            c3.metric("Bookings", stats.get("active_bookings", 0))
            c4.metric("Cancelled", stats.get("cancelled_bookings", 0))

        st.divider()
        st.markdown("### Appointments")
        svc = st.selectbox("Service", ["", "dl_appointment", "state_id", "renewal"], label_visibility="collapsed")
        if st.button("View Open Slots", use_container_width=True):
            try:
                params = {"service_type": svc} if svc else {}
                r = requests.get(f"{st.session_state['api_url']}/appointments/slots", params=params, timeout=20)
                r.raise_for_status()
                slots = r.json().get("slots", [])
                if slots:
                    for slot in slots[:8]:
                        st.markdown(f"- `{slot}`")
                else:
                    st.info("No open slots found.")
            except Exception as exc:
                st.error(f"Slots error: {exc}")

        st.divider()
        st.markdown("### Knowledge Base")
        if st.button("Rebuild Index", use_container_width=True):
            with st.spinner("Ingesting KB..."):
                try:
                    r = requests.post(f"{st.session_state['api_url']}/ingest", timeout=300)
                    r.raise_for_status()
                    st.success("Index rebuilt")
                except Exception as exc:
                    st.error(f"Ingest error: {exc}")

        st.session_state["rag_debug_query"] = st.text_input(
            "RAG debug query",
            value=st.session_state["rag_debug_query"],
            placeholder="Test retrieval for a specific question",
        )
        if st.button("Run Retrieval Debug", use_container_width=True):
            query = st.session_state.get("rag_debug_query", "").strip()
            if not query:
                st.info("Enter a query first.")
            else:
                try:
                    data = _call_retrieve(st.session_state["api_url"], message=query)
                    st.session_state["rag_hits"] = data.get("hits", [])
                except Exception as exc:
                    st.error(f"Retrieve error: {exc}")

        rag_hits = st.session_state.get("rag_hits", [])
        if rag_hits:
            st.caption("Top retrieval hits")
            for idx, hit in enumerate(rag_hits[:5], start=1):
                title = hit.get("title") or hit.get("doc_id") or "Untitled"
                sim = float(hit.get("similarity") or 0.0)
                preview = (hit.get("preview") or "").strip()
                st.markdown(f"**{idx}. {title}** ({sim:.2%})")
                if preview:
                    st.caption(preview[:180] + ("..." if len(preview) > 180 else ""))

        st.divider()
        st.markdown(
            '<div class="dps-footer">Powered by Chroma RAG and LangGraph<br>Texas DPS - CivicFlow Demo</div>',
            unsafe_allow_html=True,
        )


def _handle_user_message(prompt: str) -> None:
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            '<div class="typing-dots"><span></span><span></span><span></span></div>',
            unsafe_allow_html=True,
        )

        try:
            data = _call_chat(st.session_state["api_url"], st.session_state["session_id"], prompt)
        except Exception as exc:
            typing_placeholder.empty()
            err = f"Could not reach API: {exc}"
            st.error(err)
            st.session_state["messages"].append({"role": "assistant", "content": err, "meta": {}})
            return

        typing_placeholder.empty()

        st.session_state["session_id"] = data.get("session_id", st.session_state["session_id"])
        if data.get("name"):
            st.session_state["user_name"] = data["name"]

        answer = data.get("answer", "")
        meta = {
            "intent": data.get("intent"),
            "refusal": data.get("refusal"),
            "best_similarity": data.get("best_similarity"),
            "sources": data.get("sources", []),
            "timings_ms": data.get("timings_ms", {}),
            "stage": data.get("stage"),
        }

        msg_placeholder = st.empty()
        revealed = ""
        words = answer.split(" ")
        for idx, word in enumerate(words):
            revealed += word + " "
            if idx % 4 == 0 or idx == len(words) - 1:
                msg_placeholder.markdown(revealed)
                time.sleep(0.02)
        msg_placeholder.markdown(answer)

        _render_assistant_meta(meta)
        st.session_state["messages"].append({"role": "assistant", "content": answer, "meta": meta})


def main() -> None:
    _init_state()
    inject_css()
    _render_banner()
    _render_sidebar()

    has_messages = len(st.session_state["messages"]) > 0
    if not has_messages:
        _render_welcome()

    pending = st.session_state.get("pending_prompt")
    if pending:
        st.session_state["pending_prompt"] = None
        _handle_user_message(pending)
        return

    if has_messages:
        _render_chat_history()

    prompt = st.chat_input("Ask about DL/ID services, appointments, renewals...")
    if prompt:
        _handle_user_message(prompt)


if __name__ == "__main__":
    main()
