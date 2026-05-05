"""Streamlit interactive RAG comparison explorer."""

import streamlit as st

from src.generation.generator import OllamaGenerationClient
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.prompt_builder import build_prompt
from src.retrieval.vector_retriever import VectorRetriever
from src.visualisation import radar_data

st.set_page_config(page_title="GraphRAG vs VectorRAG", layout="wide")
st.title("GraphRAG vs VectorRAG — NordFinance Explorer")
st.caption("All inference via local Ollama · No data leaves the machine")


@st.cache_resource
def _vector_retriever() -> VectorRetriever:
    return VectorRetriever()


@st.cache_resource
def _graph_retriever() -> HybridRetriever:
    return HybridRetriever()


@st.cache_resource
def _generator() -> OllamaGenerationClient:
    return OllamaGenerationClient()


query = st.text_input(
    "Ask a question about NordFinance Group:",
    placeholder="Which officers serve on boards of companies sharing the same auditor?",
)

if query:
    vector_ret = _vector_retriever()
    hybrid_ret = _graph_retriever()
    gen = _generator()

    with st.spinner("Running VectorRAG…"):
        v_chunks = vector_ret.retrieve(query)
        v_prompt = build_prompt(query, [], v_chunks)
        v_answer = gen.generate(v_prompt)

    with st.spinner("Running GraphRAG…"):
        ctx = hybrid_ret.retrieve(query)
        g_prompt = build_prompt(query, ctx["graph"], ctx["vector"])
        g_answer = gen.generate(g_prompt)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("VectorRAG")
        st.write(v_answer)
        with st.expander("Retrieved chunks"):
            for i, c in enumerate(v_chunks):
                st.markdown(f"**Chunk {i + 1}** (dist={c['distance']:.3f})")
                st.text(c["text"][:400])

    with col2:
        st.subheader("GraphRAG")
        st.write(g_answer)
        with st.expander("Graph triples"):
            for t in ctx["graph"]:
                st.code(f"{t['source']} --[{t['rel']}]--> {t['target']}")
        with st.expander("Vector chunks"):
            for i, c in enumerate(ctx["vector"]):
                st.markdown(f"**Chunk {i + 1}**")
                st.text(c["text"][:400])

    st.divider()
    st.subheader("RAG Triad — live scores require Ollama running")
    st.info("Run `make eval` offline to compute full RAG Triad scores over 30 questions.")

    # Placeholder radar from dummy scores for UI demo
    dummy_v = {"context_relevance": 0.72, "groundedness": 0.68, "answer_relevance": 0.74}
    dummy_g = {"context_relevance": 0.81, "groundedness": 0.79, "answer_relevance": 0.82}
    v_data = radar_data(dummy_v)
    g_data = radar_data(dummy_g)

    rc1, rc2 = st.columns(2)
    with rc1:
        st.caption("VectorRAG (reference)")
        st.bar_chart(dict(zip(v_data["labels"], v_data["values"])))
    with rc2:
        st.caption("GraphRAG (reference)")
        st.bar_chart(dict(zip(g_data["labels"], g_data["values"])))
