"""Visualisation helpers for RAG Triad results (chart-data only, no renderer dep)."""

_TRIAD_KEYS = ("context_relevance", "groundedness", "answer_relevance")


def radar_data(scores: dict[str, float]) -> dict[str, list]:
    """Return labels and values for a triad radar plot."""
    return {
        "labels": list(_TRIAD_KEYS),
        "values": [scores.get(k, 0.0) for k in _TRIAD_KEYS],
    }


def score_deltas(
    vector_triads: list[float],
    graph_triads: list[float],
) -> list[float]:
    """Return per-question GraphRAG minus VectorRAG triad score deltas."""
    return [g - v for v, g in zip(vector_triads, graph_triads, strict=True)]


def summary_table(results: list[dict]) -> dict[str, dict[str, float]]:
    """Aggregate mean triad scores by query type for both pipelines."""
    groups: dict[str, dict[str, list[float]]] = {}
    for r in results:
        qt = r.get("query_type", "unknown")
        if qt not in groups:
            groups[qt] = {"vector": [], "graph": []}
        groups[qt]["vector"].append(r.get("vector", {}).get("triad", 0.0))
        groups[qt]["graph"].append(r.get("graph", {}).get("triad", 0.0))

    out: dict[str, dict[str, float]] = {}
    for qt, pipelines in groups.items():
        out[qt] = {
            "vector_mean": sum(pipelines["vector"]) / max(len(pipelines["vector"]), 1),
            "graph_mean": sum(pipelines["graph"]) / max(len(pipelines["graph"]), 1),
        }
    return out
