import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.db.errors import DatabaseUnavailable
from app.models.schemas import ErrorResponse, ExplainRequest, InvestigationResponse
from app.services.investigation import InvestigationService, TransactionNotFound
from app.services.llm_service import LLMUnavailable

logger = logging.getLogger(__name__)
router = APIRouter()


def _service(request: Request) -> InvestigationService:
    return request.app.state.service


@router.post(
    "/explain",
    response_model=InvestigationResponse,
    responses={404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
    summary="Investigate one transaction and explain its fraud risk",
)
def explain(body: ExplainRequest, request: Request):
    try:
        return _service(request).explain(body.transaction_id, include_trace=body.include_trace)
    except TransactionNotFound:
        return JSONResponse(status_code=404, content={
            "error": "transaction_not_found",
            "detail": f"Transaction {body.transaction_id} does not exist in Supabase."})
    except DatabaseUnavailable as exc:
        # Supabase is the only critical source; without the transaction there is nothing to explain.
        logger.error("Critical database unavailable: %s", exc)
        return JSONResponse(status_code=503, content={"error": "database_unavailable", "detail": str(exc)})
    except LLMUnavailable as exc:
        return JSONResponse(status_code=502, content={"error": "llm_unavailable", "detail": str(exc)})


@router.get("/health", summary="Check connectivity to Supabase, Neo4j and Qdrant")
def health(request: Request) -> dict[str, Any]:
    service = _service(request)
    checks = {
            "supabase": service.transactions.ping,
            "neo4j": service.graph.ping,
            "qdrant": service.policies.store.collection_info,
            }
    results: dict[str, Any] = {}
    for name, check in checks.items():
        try:
            results[name] = {"status": "ok", **check()}
        except Exception as exc:
            results[name] = {"status": "unavailable", "detail": f"{type(exc).__name__}: {exc}"}
    overall = "ok" if all(r["status"] == "ok" for r in results.values()) else "degraded"
    if overall != "ok":
        raise HTTPException(status_code=503, detail={"status": overall, "checks": results})
    return {"status": overall, "checks": results}
