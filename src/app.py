"""
Streamlit Chat UI for the Local Wikipedia RAG Assistant.
Provides a chat-style interface with retrieved context display and system info sidebar.
"""

import sys
import os

# Ensure project root is on the path so 'src' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.retrieval import retrieve_context, classify_query
from src.generation import generate_answer_stream, LLM_MODEL, check_llm_model
from src.embeddings import EMBEDDING_MODEL, check_embedding_model
from src.vector_store import get_store_stats

# --- Page Configuration ---
st.set_page_config(
    page_title="Local Wikipedia RAG Assistant",
    page_icon="📚",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .context-chunk {
        background-color: #f0f2f6;
        border-left: 4px solid #4CAF50;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
        font-size: 0.85em;
    }
    .query-type-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: bold;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)


# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "contexts" not in st.session_state:
    st.session_state.contexts = {}  # message_index -> retrieval_result


# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ System Info")

    # Model info
    st.subheader("Models")
    llm_available = check_llm_model()
    embed_available = check_embedding_model()

    st.write(f"**LLM:** `{LLM_MODEL}` {'✅' if llm_available else '❌'}")
    st.write(f"**Embeddings:** `{EMBEDDING_MODEL}` {'✅' if embed_available else '❌'}")

    if not llm_available:
        st.error(f"LLM not found. Run: `ollama pull {LLM_MODEL}`")
    if not embed_available:
        st.error(f"Embedding model not found. Run: `ollama pull {EMBEDDING_MODEL}`")

    # Vector store info
    st.subheader("Vector Store")
    stats = get_store_stats()
    st.write(f"**Total chunks:** {stats.get('total_chunks', 0)}")
    st.write(f"**Total entities:** {stats.get('total_entities', 0)}")
    st.write(f"**Person chunks:** {stats.get('person_chunks', 0)}")
    st.write(f"**Place chunks:** {stats.get('place_chunks', 0)}")

    if stats.get("total_chunks", 0) == 0:
        st.warning("Vector store is empty. Run ingestion first:\n```\npython scripts/ingest_data.py\n```")

    # Retrieval settings
    st.subheader("Retrieval Settings")
    n_results = st.slider("Number of chunks to retrieve", 1, 10, 5)

    # Reset button
    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.contexts = {}
        st.rerun()

    # Entity list
    if stats.get("entities"):
        with st.expander("📋 Indexed Entities"):
            for entity in stats["entities"]:
                st.write(f"• {entity}")


# --- Main Chat Interface ---
st.title("📚 Local Wikipedia RAG Assistant")
st.caption("Ask questions about famous people and places — powered by local AI")

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show context expander for assistant messages
        if message["role"] == "assistant" and i in st.session_state.contexts:
            ctx = st.session_state.contexts[i]
            query_type = ctx.get("query_type", "unknown")

            with st.expander(f"📎 Retrieved Context (type: {query_type})"):
                if ctx.get("chunks"):
                    for j, chunk in enumerate(ctx["chunks"]):
                        meta = chunk["metadata"]
                        distance = chunk.get("distance", "N/A")
                        st.markdown(f"""
**Source {j+1}: {meta['entity_name']}** (type: {meta['entity_type']}) | similarity: {1 - distance:.3f}
> {chunk['text'][:500]}{'...' if len(chunk['text']) > 500 else ''}

*Source: {meta['source_url']}* | Chunk {meta['chunk_index']+1}/{meta['total_chunks']}
---
""")
                else:
                    st.info("No relevant context was found.")


# Chat input
if prompt := st.chat_input("Ask about a famous person or place..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Retrieve context
    with st.spinner("Searching knowledge base..."):
        retrieval_result = retrieve_context(prompt, n_results=n_results)

    query_type = retrieval_result.get("query_type", "unknown")
    chunks = retrieval_result.get("chunks", [])

    # Generate answer
    with st.chat_message("assistant"):
        # Stream the response
        response = st.write_stream(
            generate_answer_stream(prompt, chunks)
        )

        # Show context
        with st.expander(f"📎 Retrieved Context (type: {query_type})"):
            if chunks:
                for j, chunk in enumerate(chunks):
                    meta = chunk["metadata"]
                    distance = chunk.get("distance", "N/A")
                    st.markdown(f"""
**Source {j+1}: {meta['entity_name']}** (type: {meta['entity_type']}) | similarity: {1 - distance:.3f}
> {chunk['text'][:500]}{'...' if len(chunk['text']) > 500 else ''}

*Source: {meta['source_url']}* | Chunk {meta['chunk_index']+1}/{meta['total_chunks']}
---
""")
            else:
                st.info("No relevant context was found.")

    # Save to session state
    msg_index = len(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.contexts[msg_index] = retrieval_result
