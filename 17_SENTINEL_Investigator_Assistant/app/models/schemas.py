"""Request / response models.

Two groups:
  * LLMExplanation  - the JSON the LLM must return (validated before use)
  * InvestigationResponse - what the API returns, which separates
        database_facts      (written by code from retrieved records)
        llm_interpretation  (written by the LLM)
"""
from typing import Any, Literal

from pydantic import BaseModel, Field

Action = Literal["ALLOW", "MANUAL_REVIEW", "ESCALATE"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


# ----------------------------------------------------------------- request

class ExplainRequest(BaseModel):
    transaction_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_\-]+$",
                                examples=["TX_0000082052"])
    include_trace: bool = Field(False, description="Include the full retrieved evidence for debugging")


# ----------------------------------------------------------------- LLM output

class LLMReasonCode(BaseModel):
    code: str = Field(description="One of the SUPPORTED reason codes given in the prompt")
    explanation: str = Field(description="Why this code matters for this transaction, citing the facts")


class LLMCitation(BaseModel):
    source_document: str = Field(description="source_document of a retrieved policy chunk")
    chunk_number: int = Field(description="chunk_number of that retrieved policy chunk")
    how_it_applies: str = Field(description="What the chunk says that applies here")


class LLMExplanation(BaseModel):
    risk_level: RiskLevel
    recommended_action: Action
    summary: str = Field(description="2-4 sentence explanation of the transaction risk")
    reason_codes: list[LLMReasonCode]
    citations: list[LLMCitation]
    investigation_steps: list[str] = Field(description="Concrete checks for the human investigator")
    missing_information: list[str] = Field(description="Evidence that is missing or unknown")


# ----------------------------------------------------------------- API response

class ReasonCodeFinding(BaseModel):
    code: str
    description: str
    source: str = Field(description="Database the supporting evidence came from")
    evidence: str = Field(description="Database values that trigger the code (written by code, not the LLM)")
    llm_explanation: str


class Citation(BaseModel):
    source_document: str
    chunk_number: int
    title: str | None
    document_type: str | None
    topic: str | None
    rank: int
    score: float
    how_it_applies: str


class LLMInterpretation(BaseModel):
    risk_level: RiskLevel
    summary: str
    investigation_steps: list[str]


class EvidenceStatus(BaseModel):
    transaction: Literal["ok"]
    features: Literal["ok", "missing"]
    graph: Literal["ok", "customer_not_in_graph", "unavailable"]
    policy: Literal["ok", "no_results", "unavailable"]


class ValidationReport(BaseModel):
    removed_reason_codes: list[str] = []
    removed_citations: list[str] = []
    action_adjustments: list[str] = []
    llm_attempts: int = 1


class InvestigationResponse(BaseModel):
    transaction_id: str
    recommended_action: Action
    insufficient_evidence: bool
    database_facts: list[str]
    supported_reason_codes: list[str] = Field(description="All codes the retrieved evidence supports")
    reason_codes: list[ReasonCodeFinding] = Field(description="Codes the LLM selected, after validation")
    llm_interpretation: LLMInterpretation
    citations: list[Citation]
    missing_information: list[str]
    evidence_status: EvidenceStatus
    validation: ValidationReport
    policy_query: str | None
    models: dict[str, str]
    processing_time_ms: int
    disclaimer: str
    evidence_trace: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: str
    detail: str
