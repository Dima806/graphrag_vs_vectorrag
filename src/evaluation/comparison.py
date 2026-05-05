"""Side-by-side VectorRAG vs GraphRAG evaluation runner."""

import argparse
import json
from pathlib import Path

from loguru import logger

from src.config import get_settings
from src.evaluation.question_bank import QUESTION_BANK, EvalQuestion
from src.evaluation.rag_triad import RAGTriad
from src.generation.generator import OllamaGenerationClient
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.prompt_builder import build_prompt
from src.retrieval.vector_retriever import VectorRetriever


def _run_vector(
    query: str,
    retriever: VectorRetriever,
    generator: OllamaGenerationClient,
) -> tuple[str, str]:
    """VectorRAG pipeline: retrieve chunks → generate. Returns (answer, context)."""
    chunks = retriever.retrieve(query)
    context = "\n\n".join(c["text"] for c in chunks)
    prompt = build_prompt(query, [], chunks)
    return generator.generate(prompt), context


def _run_graph(
    query: str,
    retriever: HybridRetriever,
    generator: OllamaGenerationClient,
) -> tuple[str, str]:
    """GraphRAG pipeline: retrieve triples + chunks → generate. Returns (answer, context)."""
    ctx = retriever.retrieve(query)
    triples = ctx["graph"]
    chunks = ctx["vector"]
    prompt = build_prompt(query, triples, chunks)
    graph_lines = [f"{t['source']} --[{t['rel']}]--> {t['target']}" for t in triples]
    context = "\n".join(graph_lines) + "\n\n" + "\n\n".join(c["text"] for c in chunks)
    return generator.generate(prompt), context


def evaluate_question(
    q: EvalQuestion,
    vector_retriever: VectorRetriever,
    graph_retriever: HybridRetriever,
    generator: OllamaGenerationClient,
    triad: RAGTriad,
) -> dict:
    """Evaluate a question on both pipelines; return structured result."""
    v_answer, v_context = _run_vector(q.question, vector_retriever, generator)
    g_answer, g_context = _run_graph(q.question, graph_retriever, generator)
    v_scores = triad.evaluate(q.question, v_context, v_answer)
    g_scores = triad.evaluate(q.question, g_context, g_answer)
    return {
        "question": q.question,
        "query_type": q.query_type,
        "vector": {"answer": v_answer, **v_scores},
        "graph": {"answer": g_answer, **g_scores},
    }


def main(smoke: bool = False) -> None:
    """Run evaluation over the question bank and write results to data/eval/."""
    questions = QUESTION_BANK[:3] if smoke else QUESTION_BANK
    vector_retriever = VectorRetriever()
    graph_retriever = HybridRetriever()
    generator = OllamaGenerationClient()
    triad = RAGTriad()

    results = []
    for q in questions:
        logger.info(f"Evaluating [{q.query_type}]: {q.question[:70]!r}")
        results.append(evaluate_question(q, vector_retriever, graph_retriever, generator, triad))

    out_dir = Path(get_settings().eval.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = "smoke_results.json" if smoke else "comparison.json"
    (out_dir / fname).write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info(f"Results written to {out_dir / fname}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAG Triad evaluation.")
    parser.add_argument("--smoke", action="store_true", help="Run 3-question smoke test.")
    args = parser.parse_args()
    main(smoke=args.smoke)
