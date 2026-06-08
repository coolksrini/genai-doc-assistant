"""
GenAI Document Assistant — Streamlit UI
Connects to the FastAPI backend at API_BASE_URL (default: http://localhost:8000).
"""
import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

ACCEPTED_TYPES = ["pdf", "txt", "csv", "xlsx", "json", "yaml"]

st.set_page_config(
    page_title="GenAI Document Assistant",
    page_icon="🤖",
    layout="wide",
)


# ---------- helpers ----------

def check_health() -> dict | None:
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return r.json()
    except Exception:
        return None


def upload_document(file) -> dict | None:
    try:
        r = requests.post(
            f"{API_BASE_URL}/upload-document",
            files={"file": (file.name, file.getvalue(), file.type or "application/octet-stream")},
            timeout=60,
        )
        return r.json(), r.status_code
    except Exception as exc:
        return {"detail": str(exc)}, 500


def ask_question(question: str, top_k: int) -> dict | None:
    try:
        r = requests.post(
            f"{API_BASE_URL}/ask-questions",
            json={"question": question, "top_k": top_k},
            timeout=120,
        )
        return r.json(), r.status_code
    except Exception as exc:
        return {"detail": str(exc)}, 500


# ---------- health banner ----------

health = check_health()
if health is None:
    st.error(
        f"Cannot reach the API at `{API_BASE_URL}`. "
        "Make sure the FastAPI server is running (`python main.py`).",
        icon="🔴",
    )
    st.stop()

if health.get("status") == "degraded":
    msgs = []
    if health.get("llm") == "unavailable":
        msgs.append("LLM (Ollama) is unavailable")
    if health.get("vector_store") == "unavailable":
        msgs.append("Vector store is unavailable")
    st.warning("System degraded: " + "; ".join(msgs), icon="⚠️")
else:
    st.success(f"API connected — v{health.get('version', '?')} | LLM: {health.get('llm')} | Store: {health.get('vector_store')}", icon="✅")


# ---------- layout ----------

st.title("🤖 GenAI Document Assistant")
st.caption("Upload enterprise documents and ask questions — answers grounded in your documents only.")

col_upload, col_qa = st.columns([1, 2], gap="large")


# ---------- sidebar / upload ----------

with col_upload:
    st.subheader("📁 Upload Documents")
    uploaded = st.file_uploader(
        "Choose a file",
        type=ACCEPTED_TYPES,
        help=f"Supported: {', '.join(ACCEPTED_TYPES)}. Max 10 MB.",
    )

    if uploaded:
        with st.spinner(f"Ingesting {uploaded.name}…"):
            result, status = upload_document(uploaded)

        if status == 200:
            st.success(
                f"✅ **{result['filename']}** ingested — {result['chunk_count']} chunks",
                icon="📄",
            )
        else:
            st.error(f"Upload failed: {result.get('detail', 'unknown error')}", icon="❌")

    st.divider()
    st.caption("**Tip:** Upload multiple documents before asking questions. The system searches across all of them.")


# ---------- Q&A ----------

with col_qa:
    st.subheader("💬 Ask a Question")

    question = st.text_area(
        "Your question",
        placeholder="e.g. What is the main topic of the document?",
        height=100,
        key="question_input",
    )
    top_k = st.slider("Chunks to retrieve", min_value=1, max_value=20, value=5, key="top_k")
    submitted = st.button("Ask", use_container_width=True, type="primary", key="ask_btn")

    if submitted:
        if not question.strip():
            st.warning("Please enter a question.", icon="⚠️")
        else:
            with st.spinner("Thinking…"):
                result, status = ask_question(question.strip(), top_k)

            if status == 200:
                is_grounded = result.get("is_grounded", False)

                # Answer
                if is_grounded:
                    st.success("**Answer**")
                    st.markdown(result["answer"])
                else:
                    st.info(result["answer"], icon="🔍")

                # Sources
                sources = result.get("sources", [])
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)} chunk(s))", expanded=True):
                        for i, src in enumerate(sources, 1):
                            st.markdown(
                                f"**{i}. {src['document_name']}** — chunk {src['chunk_index']}"
                            )
                            st.caption(src["excerpt"])
                            if i < len(sources):
                                st.divider()

                # Agent trace
                trace = result.get("agent_trace", [])
                if trace:
                    with st.expander("🔎 Agent Steps", expanded=False):
                        for step in trace:
                            st.text(step)

            elif status == 400:
                st.warning(result.get("detail", "Bad request"), icon="⚠️")
            elif status == 503:
                st.error(result.get("detail", "Service unavailable"), icon="🔴")
            else:
                st.error(f"Unexpected error ({status}): {result.get('detail')}", icon="❌")
