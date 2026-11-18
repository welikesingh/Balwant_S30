"""Policy retrieval evaluation: Hit@5 at document and chunk level.

    uv run python evaluation/evaluate_retrieval.py

Hit@5 = questions with at least one relevant result in the top 5 / total questions.

The search is the application's own PolicyRetriever.search_policy (same embedding
model, task type, dimensions and default document-type filter). For comparison we also
report the same search over the whole collection (no document-type filter).
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.db.qdrant_db import QdrantStore  # noqa: E402
from app.services.policy_retriever import GeminiEmbedder, PolicyRetriever  # noqa: E402

QUESTIONS_FILE = ROOT / "evaluation" / "retrieval_questions.json"
RESULTS_FILE = ROOT / "evaluation" / "retrieval_results.json"
TOP_K = 5


def verify_ground_truth(store: QdrantStore, questions: list[dict]) -> None:
    """Every expected chunk must still exist and contain its answer phrase."""
    points, _ = store._client.scroll(store.collection, limit=1000, with_payload=True, with_vectors=False)
    text_by_chunk = {f"{p.payload['source_document']}#{p.payload['chunk_number']}": p.payload["text"]
                     for p in points}
    for q in questions:
        found = sorted(key for key, text in text_by_chunk.items()
                       if any(phrase in text for phrase in q["answer_phrases"]))
        if found != q["expected_chunks"]:
            raise SystemExit(f"{q['id']}: expected chunks no longer match the collection")


def score(hits: list[dict], question: dict) -> dict:
    expected_docs = set(question["expected_documents"])
    expected_chunks = set(question["expected_chunks"])
    ranked = []
    for hit in hits:
        key = f"{hit['source_document']}#{hit['chunk_number']}"
        ranked.append({
            "rank": hit["rank"], "score": hit["score"], "source_document": hit["source_document"],
            "chunk_number": hit["chunk_number"], "point_id": hit["point_id"],
            "document_type": hit["document_type"], "topic": hit["topic"], "title": hit["title"],
            "document_relevant": hit["source_document"] in expected_docs,
            "chunk_relevant": key in expected_chunks,
        })
    first_doc = next((r["rank"] for r in ranked if r["document_relevant"]), None)
    first_chunk = next((r["rank"] for r in ranked if r["chunk_relevant"]), None)
    return {"document_hit": first_doc is not None, "chunk_hit": first_chunk is not None,
            "first_relevant_document_rank": first_doc, "first_relevant_chunk_rank": first_chunk,
            "results": ranked}


def main() -> None:
    settings = get_settings()
    spec = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    questions = spec["questions"]

    store = QdrantStore(settings.qdrant_url, settings.qdrant_api_key.get_secret_value(),
                        settings.qdrant_collection)
    verify_ground_truth(store, questions)
    embedder = GeminiEmbedder(settings.gemini_api_key.get_secret_value(), settings.embedding_model,
                              settings.embedding_dim, settings.embedding_query_task)
    retriever = PolicyRetriever(embedder, store, settings.policy_document_types)

    configurations = {
        "app_default_filter": settings.policy_document_types,   # what /explain uses
        "whole_collection": [],                                  # no filter
    }
    report = {"collection": settings.qdrant_collection, "embedding_model": settings.embedding_model,
              "top_k": TOP_K, "relevance_definition": spec["relevance_definition"], "configurations": {}}

    for name, doc_types in configurations.items():
        per_question = []
        for q in questions:
            started = time.perf_counter()
            hits = retriever.search_policy(q["question"], top_k=TOP_K, document_types=doc_types)
            result = score(hits, q)
            per_question.append({"id": q["id"], "question": q["question"],
                                 "expected_documents": q["expected_documents"],
                                 "latency_ms": int((time.perf_counter() - started) * 1000), **result})
        n = len(per_question)
        doc_hits = sum(r["document_hit"] for r in per_question)
        chunk_hits = sum(r["chunk_hit"] for r in per_question)
        report["configurations"][name] = {
            "document_types_filter": doc_types or "none",
            "document_hit_at_5": round(doc_hits / n, 3), "document_hits": doc_hits,
            "chunk_hit_at_5": round(chunk_hits / n, 3), "chunk_hits": chunk_hits,
            "questions": n, "per_question": per_question,
        }
        print(f"{name}: document Hit@5 {doc_hits}/{n}, chunk Hit@5 {chunk_hits}/{n}")
        for r in per_question:
            print(f"  {r['id']} doc={'Y' if r['document_hit'] else 'N'} chunk={'Y' if r['chunk_hit'] else 'N'} "
                  f"first_doc_rank={r['first_relevant_document_rank']} "
                  f"top1={r['results'][0]['source_document']}#{r['results'][0]['chunk_number']} "
                  f"({r['results'][0]['score']})")

    RESULTS_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {RESULTS_FILE}")


if __name__ == "__main__":
    main()
