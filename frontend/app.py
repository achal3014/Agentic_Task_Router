"""
Knowva — The Knowledge Assistant
Streamlit frontend for the multi-agent knowledge assistant.
"""

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/route"

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Knowva",
    page_icon="🔮",
    layout="centered",
)

# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_escalation" not in st.session_state:
    st.session_state.show_escalation = False


# ─────────────────────────────────────────────
# Document text extraction
# ─────────────────────────────────────────────
def extract_text(file_bytes: bytes, filename: str) -> str:
    filename_lower = filename.lower()
    if filename_lower.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1").strip()
    elif filename_lower.endswith(".pdf"):
        try:
            import fitz

            text_parts = []
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text = page.get_text().strip()
                if text:
                    text_parts.append(text)
            doc.close()
            return (
                "\n\n".join(text_parts)
                if text_parts
                else "Could not extract text from this PDF."
            )
        except ImportError:
            return "PDF support requires PyMuPDF. Run: pip install pymupdf"
        except Exception as e:
            return f"Could not read PDF: {str(e)}"
    return f"Unsupported format: {filename}"


# ─────────────────────────────────────────────
# API call
# ─────────────────────────────────────────────
def call_api(user_input: str, session_id=None, document: str = None) -> dict:
    payload = {"user_input": user_input}
    if session_id:
        payload["session_id"] = session_id
    if document:
        payload["document"] = document
    try:
        r = requests.post(API_URL, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {
            "error": "Cannot connect to backend. Is the server running?",
            "task_type": "error",
            "response": "",
        }
    except Exception as e:
        return {"error": str(e), "task_type": "error", "response": ""}


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.title("🔮 Knowva")
st.caption(
    "Your intelligent knowledge assistant — Ask anything, summarize, translate, or research any topic."
)

# ─────────────────────────────────────────────
# Agent guide
# ─────────────────────────────────────────────
with st.expander("📖 How to use Knowva — Agent Guide"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📋 Summarizer**")
        st.caption("Paste text or upload a file and ask to summarize.")
        st.code("Summarize this: [paste text]\nor upload a PDF/TXT file", language=None)

        st.markdown("**💬 QnA**")
        st.caption("Ask any question with or without a document.")
        st.code(
            "What is gradient descent?\nor\nExplain this. Document: [text]",
            language=None,
        )

    with col2:
        st.markdown("**🌐 Translator**")
        st.caption("Translate text to or from any language.")
        st.code("Translate to Spanish: [text]", language=None)

        st.markdown("**🔍 Research**")
        st.caption(
            "Use 'research', 'look up', or 'find information about' for deep research."
        )
        st.code("Research the history of the internet", language=None)

    st.info(
        "💡 **Pro tip:** After any QnA answer, click **Go Deeper →** to get a full research-level response."
    )
    st.warning(
        "⚠️ If a document is uploaded, Research mode is disabled — use QnA or Summarizer instead."
    )


# ─────────────────────────────────────────────
# Chat history
# ─────────────────────────────────────────────
AGENT_ICONS = {
    "qna": "💬",
    "summarize": "📋",
    "translate": "🌐",
    "research": "🔍",
    "unsupported": "⚠️",
    "error": "❌",
}

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
            if msg.get("has_document"):
                st.caption(f"📎 Document attached: {msg.get('filename', 'file')}")
    else:
        data = msg["data"]
        task = data.get("task_type", "unsupported")
        icon = AGENT_ICONS.get(task, "🤖")
        with st.chat_message("assistant", avatar=icon):
            response_text = data.get("response") or data.get("error") or ""
            escalation_line = "Would you like a more in-depth analysis? I can route this to the Research agent for a comprehensive answer."
            response_text = response_text.replace(escalation_line, "").strip()
            st.write(response_text)

            meta_cols = st.columns(4)
            with meta_cols[0]:
                st.caption(f"Agent: **{task}**")
            with meta_cols[1]:
                if data.get("confidence") is not None:
                    st.caption(f"Confidence: **{int(data['confidence'] * 100)}%**")
            with meta_cols[2]:
                if data.get("cost_usd") is not None:
                    st.caption(f"Cost: **${data['cost_usd']:.6f}**")
            with meta_cols[3]:
                tools = data.get("tools_called")
                if tools and task == "research":
                    st.caption(f"Tools: **{', '.join(tools)}**")

# ─────────────────────────────────────────────
# Escalation button
# ─────────────────────────────────────────────
if st.session_state.show_escalation:
    st.divider()
    col_btn, col_hint = st.columns([1, 3])
    with col_btn:
        if st.button("🔍 Go Deeper →", key="escalation_btn"):
            st.session_state.show_escalation = False
            with st.spinner("Researching with tools..."):
                result = call_api("yes please", session_id=st.session_state.session_id)
            if result.get("session_id"):
                st.session_state.session_id = result["session_id"]
            st.session_state.messages.append({"role": "user", "content": "yes please"})
            st.session_state.messages.append({"role": "assistant", "data": result})
            st.session_state.show_escalation = result.get("escalation_offer", False)
            st.rerun()
    with col_hint:
        st.caption(
            "Get a comprehensive research-level answer with Wikipedia, ArXiv, and web search tools."
        )

# ─────────────────────────────────────────────
# Input area
# ─────────────────────────────────────────────

uploaded_file = st.file_uploader(
    "📎 Attach a document (optional — PDF or TXT)",
    type=["pdf", "txt"],
    key="file_uploader",
    label_visibility="visible",
)

document_text = None
if uploaded_file is not None:
    document_text = extract_text(uploaded_file.read(), uploaded_file.name)
    if (
        document_text
        and not document_text.startswith("Could not")
        and not document_text.startswith("Unsupported")
        and not document_text.startswith("PDF support")
    ):
        st.success(
            f"✅ Document loaded: {uploaded_file.name} ({len(document_text)} characters)"
        )
    else:
        st.error(document_text)
        document_text = None

user_input = st.chat_input(
    "Ask a question, paste text to summarize, or say 'Research...' to explore any topic..."
)

if user_input and user_input.strip():
    st.session_state.show_escalation = False

    with st.spinner("Thinking..."):
        result = call_api(
            user_input.strip(),
            session_id=st.session_state.session_id,
            document=document_text,
        )

    if result.get("session_id"):
        st.session_state.session_id = result["session_id"]

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input.strip(),
            "has_document": document_text is not None,
            "filename": uploaded_file.name if uploaded_file else None,
        }
    )
    st.session_state.messages.append(
        {
            "role": "assistant",
            "data": result,
        }
    )

    if result.get("escalation_offer"):
        st.session_state.show_escalation = True

    st.rerun()

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔮 Knowva")
    st.caption("Intelligent knowledge assistant")
    st.divider()

    if st.session_state.session_id:
        st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
    else:
        st.caption("No active session")

    if st.button("🗑 Clear conversation", key="clear_btn"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.show_escalation = False
        st.rerun()

    st.divider()
    st.caption("Powered by Groq · LangGraph · ChromaDB · Redis")
