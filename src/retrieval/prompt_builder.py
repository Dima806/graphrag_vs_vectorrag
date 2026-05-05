"""Context assembly with hard token budget for qwen2.5:1.5b."""

from src.config import get_settings


def count_tokens(text: str) -> int:
    """Approximate token count using a 4-chars-per-token heuristic."""
    return len(text) // 4


def build_prompt(
    query: str,
    graph_triples: list[dict],
    vector_chunks: list[dict],
    budget: int | None = None,
) -> str:
    """Assemble a retrieval-augmented prompt within the token budget.

    Graph triples are prepended; vector chunks fill remaining budget.
    """
    if budget is None:
        budget = get_settings().retrieval.context_budget_tokens

    parts: list[str] = []

    if graph_triples:
        lines = [f"- {t['source']} --[{t['rel']}]--> {t['target']}" for t in graph_triples]
        parts.append("Knowledge graph context:\n" + "\n".join(lines))

    for chunk in vector_chunks:
        candidate_text = f"Document excerpt:\n{chunk['text']}"
        joined = "\n\n".join([*parts, candidate_text])
        if count_tokens(joined) <= budget:
            parts.append(candidate_text)

    context = "\n\n".join(parts) if parts else "No relevant context found."
    return f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
