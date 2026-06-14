from __future__ import annotations

import os

import requests
import streamlit as st

try:
    from .env import load_dotenv_file
except ImportError:
    from env import load_dotenv_file


load_dotenv_file()
API_BASE_URL = os.getenv("INSIGHT_API_BASE_URL", "http://localhost:8000").rstrip("/")
APP_TITLE = "Document Analysis RAG"


def api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def raise_for_status_with_detail(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise requests.HTTPError(f"{exc} - {detail}", response=response) from exc


def load_index_options() -> list[dict]:
    try:
        response = requests.get(api_url("/indexes"), timeout=20)
        raise_for_status_with_detail(response)
        return response.json().get("indexes", [])
    except requests.RequestException as exc:
        st.sidebar.error(f"API unavailable: {exc}")
        return []


def upload_index(index_id: str, uploaded_files) -> dict:
    files = [
        ("files", (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream"))
        for uploaded_file in uploaded_files
    ]
    response = requests.post(api_url("/indexes"), data={"index_id": index_id}, files=files, timeout=300)
    raise_for_status_with_detail(response)
    return response.json()


def delete_index(index_id: str) -> None:
    response = requests.delete(api_url(f"/indexes/{index_id}"), timeout=20)
    raise_for_status_with_detail(response)


def chat(index_id: str, message: str) -> dict:
    response = requests.post(api_url("/chat"), json={"index_id": index_id, "message": message}, timeout=180)
    raise_for_status_with_detail(response)
    return response.json()


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander("Sources"):
        for source in sources:
            score = source["score"] if source["score"] is not None else "n/a"
            st.markdown(f"**{source['filename']}** ({source['type']}, score: `{score}`)")
            st.caption(source["text"])


st.set_page_config(page_title=APP_TITLE)

st.markdown(
    """
    <style>
    :root {
        --app-accent: #2563eb;
        --app-accent-hover: #1d4ed8;
        --app-success-bg: rgba(22, 101, 52, 0.22);
        --app-success-text: #86efac;
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(148, 163, 184, 0.18);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        letter-spacing: 0;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: 650;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--app-accent);
        border-color: var(--app-accent);
        color: #ffffff;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: var(--app-accent-hover);
        border-color: var(--app-accent-hover);
        color: #ffffff;
    }
    [data-testid="stSidebar"] [data-testid="stAlert"] {
        border-radius: 8px;
        padding: 0.65rem 0.8rem;
    }
    [data-testid="stSidebar"] .stFileUploader section {
        padding: 0.8rem;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] .stFileUploader section button {
        border-radius: 8px;
    }
    [data-testid="stSidebar"] hr {
        margin: 1rem 0;
        border-color: rgba(148, 163, 184, 0.22);
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border-radius: 8px;
        border-color: rgba(148, 163, 184, 0.28);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(APP_TITLE)

if st.session_state.get("active_index"):
    st.success(f"Active index: **{st.session_state.active_index}** - Ready to answer questions")
else:
    st.warning("No index loaded - upload documents or load an existing index from the sidebar")

with st.sidebar:
    st.header("Documents")

    if st.session_state.get("active_index"):
        st.success(f"Active collection: {st.session_state.active_index}")
    else:
        st.info("Upload files or choose a saved collection.")

    st.subheader("Upload")
    st.caption("PDF, DOCX, and XLSX files are supported.")

    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "xlsx", "xls"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    index_name = st.text_input(
        "Collection name",
        value="demo-documents",
        help="Use a short name you will recognize later.",
    )

    if st.button("Create collection", type="primary"):
        if not uploaded_files:
            st.error("Please upload at least one document")
        elif not index_name.strip():
            st.error("Please enter a collection name")
        else:
            with st.spinner("Uploading and indexing documents..."):
                try:
                    result = upload_index(index_name, uploaded_files)
                    st.session_state.active_index = result["index_id"]
                    st.success(f"Created collection with {len(result['documents'])} document(s)")
                    for warning in result.get("warnings", []):
                        st.warning(warning)
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(f"Could not create collection: {exc}")

    st.divider()
    st.subheader("Saved Collections")
    indexes = load_index_options()

    if not indexes:
        st.info("No saved collections yet.")
    else:
        index_options = [item["index_id"] for item in indexes]
        index_by_id = {item["index_id"]: item for item in indexes}
        active_index = st.session_state.get("active_index")
        default_index = index_options.index(active_index) if active_index in index_options else 0
        selected_index = st.selectbox("Saved collections", index_options, index=default_index)

        if st.button("Use this collection"):
            st.session_state.active_index = selected_index
            st.success(f"Using {selected_index}")
            st.rerun()

        selected_documents = index_by_id[selected_index].get("documents", [])
        with st.expander(f"View files ({len(selected_documents)})"):
            for doc in index_by_id[selected_index].get("documents", []):
                st.write(f"- {doc['filename']} ({doc['type']})")

        st.divider()
        with st.expander("Manage saved collections"):
            st.warning("Deleting a collection removes its saved search index.")
            remove_index_name = st.selectbox("Collection to delete", index_options, key="remove_select")
            if st.button("Delete selected collection"):
                try:
                    delete_index(remove_index_name)
                    if st.session_state.get("active_index") == remove_index_name:
                        for key in ["messages", "active_index"]:
                            st.session_state.pop(key, None)
                    st.success(f"{remove_index_name} deleted")
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(f"Could not delete collection: {exc}")

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Upload documents or load an existing collection to get started.",
        "sources": [],
    }]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        render_sources(msg.get("sources", []))

if prompt := st.chat_input("Ask about your documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        sources = []
        if not st.session_state.get("active_index"):
            reply = "Index documents first."
        else:
            with st.spinner("Thinking..."):
                try:
                    result = chat(st.session_state.active_index, prompt)
                    reply = result["answer"]
                    sources = result.get("sources", [])
                except requests.RequestException as exc:
                    reply = f"Chat failed: {exc}"

        st.write(reply)
        render_sources(sources)

    st.session_state.messages.append({"role": "assistant", "content": reply, "sources": sources})
