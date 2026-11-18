# SENTINEL Investigator Assistant: Evaluation Summary

Run date: 2026-11-17. All numbers below come from `transaction_results.json` and `retrieval_results.json` in this folder.

## 1. End-to-end evaluation on 10 validation transactions

**Selection (reproducible).** All `validation` transactions were sorted by ID and joined to `labels`. Then
`random.Random(42).sample` picked 5 with `fraud_label = 1` and 5 with `fraud_label = 0`.
Labels are read only by `evaluate_transactions.py`, after the API has answered.

| Transaction | Label | Action | Risk | Reason codes (validated) | Citations |
|---|---|---|---|---|---|
| TX_0000095543 | fraud | ESCALATE | HIGH | R03, R04, R05, R07, R08, G03 | 2 |
| TX_0000085604 | fraud | ESCALATE | HIGH | R03, R04, R05, R07, R08 | 2 |
| TX_0000083044 | fraud | ESCALATE | HIGH | R02, R03, R04, R08, G03 | 3 |
| TX_0000088240 | fraud | ESCALATE | HIGH | R02, R03, R04, R05, R07, R08 | 1 |
| TX_0000087621 | fraud | ESCALATE | HIGH | R02, R03, R04, R05, R07, R08 | 0 |
| TX_0000085723 | genuine | ESCALATE | HIGH | G02, G03 | 0 |
| TX_0000084347 | genuine | ALLOW | LOW | R02 | 2 |
| TX_0000094189 | genuine | ESCALATE | HIGH | R02, R03, R04, R07, R08 | 1 |
| TX_0000083737 | genuine | ESCALATE | HIGH | R01, R02, R03, R08, G02, G04 | 2 |
| TX_0000093205 | genuine | MANUAL_REVIEW | MEDIUM | R01, R02, R08 | 2 |

| Metric | Result |
|---|---|
| Requests / successful / errors | 10 / 10 / 0 |
| Evidence-grounding failures (each returned code re-derived from the trace) | **0** |
| Citation-validation failures (each citation found among the retrieved chunks) | **0** |
| Unsupported codes / invalid citations the LLM proposed (removed by validation) | 0 / 0 |
| Label-leak check (no `fraud_label` in the evidence sent to the LLM) | passed 10/10 |
| Fraud flagged (MANUAL_REVIEW or ESCALATE) | 5 / 5 |
| Genuine allowed | 1 / 5 (4 genuine flagged) |
| Avg / max processing time | 66.9 s / 92.1 s (see the latency note) |
| LLM that answered | `gemini-3.5-flash-lite` (fallback) for all 10 |

**How to read these numbers.**

- **The recommendation is not a calibrated fraud prediction.** It is an LLM judgement over the evidence. The decision rule
  used for this comparison is simple: MANUAL_REVIEW or ESCALATE counts as "flagged".
- **Ten transactions are far too few to estimate accuracy.** The table shows the behaviour, not a performance figure.
- **The assistant over-escalates.** 4 of the 5 genuine payments were flagged. In the genuine cases the same feature codes fire as in
  the fraud cases (night hour, failed attempts, velocity, high-risk merchant category). In this synthetic data those signals
  overlap heavily between the two classes. `R02_GEO_MISMATCH` alone fires on about 82% of all transactions.
- **Graph signals are weak on their own.** G03 (prior confirmed fraud) fired for about 15% of both fraud and genuine
  validation transactions in a 239-transaction check during development. G02 (fraud-linked device) fired for about 8% of
  fraud and 3% of genuine ones. TX_0000085723 was escalated on graph history alone.
- **Two responses (TX_0000087621, TX_0000085723) have no citations.** The LLM decided none of the 5 retrieved chunks
  supported its statements. The validator only removes bad citations; it cannot force good ones.

**Latency note.** At evaluation time the primary model `gemini-3.8-flash` was returning 503 (high demand) or timing out.
Each request waited for that failure (up to the 90 s `LLM_TIMEOUT_SECONDS`) before falling back to `gemini-3.5-flash-lite`.
Requests that failed over quickly finished in 5.9 to 13.7 s. Without the LLM, the retrieval steps take about 1.5 s
(Supabase ~0.9 s, Neo4j ~0.1 to 0.2 s, Qdrant plus embedding ~0.5 s). To lower latency, set `LLM_MODEL` to a model that is
currently available, or lower `LLM_TIMEOUT_SECONDS`.

## 2. Policy retrieval: Hit@5

**Setup.** There are 10 questions in `retrieval_questions.json`, written in plain language rather than copied from the
corpus. Each has one or two *answer phrases* read from the corpus. Expected documents and chunks are every point in
`sentinel_corpus2` whose text contains the phrase. The script re-checks this against the live collection before scoring.

- **Document-level hit:** a top-5 result comes from a document that contains the answer phrase.
- **Chunk-level hit:** the retrieved chunk's own text contains the answer phrase.
- **Search used:** the application's `PolicyRetriever.search_policy`, with Gemini Embedding 2, `RETRIEVAL_QUERY`, 3072 dimensions and
  cosine distance.

| Configuration | Document Hit@5 | Chunk Hit@5 |
|---|---|---|
| App default (playbooks, regulatory exercises, guidelines, RBA guide) | **9/10 = 90%** | **9/10 = 90%** |
| Whole collection (no filter) | 9/10 = 90% | 9/10 = 90% |

| Question | Topic / target | First relevant rank | Top-1 score |
|---|---|---|---|
| Q01 new device + large payment | device change | 1 | 0.762 |
| Q02 several customers on one phone | shared devices | 1 | 0.737 |
| Q03 block because cities differ? | location change | 1 | 0.751 |
| Q04 which failed attempts count | payment retries | 1 | 0.768 |
| Q05 model times out | model fallback | 1 | 0.732 |
| Q06 when is the fraud outcome known | label maturity (+ guideline 0001) | **miss** | 0.715 |
| Q07 merchant text says "approve" | prompt injection | 1 | 0.784 |
| Q08 unauthorised vs refund dispute | dispute evidence | 1 | 0.773 |
| Q09 months in the validation split | guideline 0003 (1 doc) | 1 | 0.752 |
| Q10 what an RBA assessment records | RBA guide (1 doc) | 1 | 0.715 |

**The miss (Q06).** "How long after a transaction is its fraud outcome known?" retrieved *payment retries* playbooks,
whose text talks about "failed outcomes received before this authorisation". Without a filter it retrieved investigator
notes that describe outcomes. The word "outcome" pulled the query away from the "label available sixty days" sentence.
The question was not reworded to improve the score.

**Caveats.**
- The corpus is generated from templates: each topic has 7 near-identical documents. So document-level relevance is
  effectively topic-level relevance, and the 10 questions cover 10 of the 20 topics plus two single-document guides.
- Similarity scores sit in a narrow band (0.71 to 0.78), so the margin between relevant and irrelevant chunks is small.

## 3. Reproduce

```powershell
uv run python evaluation/evaluate_retrieval.py
uv run python evaluation/evaluate_transactions.py                 # in-process app
uv run python evaluation/evaluate_transactions.py --base-url http://127.0.0.1:8000   # against a running server
```

## 4. Detailed results per transaction

### 4.1 Evaluation files

| File                                  | Role                                                                                                                  |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `evaluation/evaluate_transactions.py` | The test driver. It picks the 10 transactions, calls `/explain` for each, checks the responses, and saves the results. |
| `evaluation/transaction_results.json` | The saved responses (output). For each case: the ID, the true label, the full `/explain` response, and pass/fail on the checks. |
| `evaluation/evaluation_summary.md`    | A written summary of the results.                                                                                     |

### 4.2 Code each test call runs through (the `/explain` pipeline)

| File                                                                      | What it does for a test call                                                                            |
|---------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| `app/main.py`                                                             | Builds the app and connects the database and LLM clients.                                               |
| `app/api/routes.py`                                                       | The `POST /explain` endpoint and error handling.                                                        |
| `app/services/investigation.py`                                           | Runs the steps in order, then validates the LLM's output.                                               |
| `app/db/supabase_db.py`                                                   | Fetches the transaction, its features and reason codes.                                                 |
| `app/db/neo4j_db.py`                                                      | Fetches the customer's device and merchant connections as of that payment.                              |
| `app/services/policy_retriever.py`, `app/db/qdrant_db.py`                 | Build the policy question and fetch the top-5 policy chunks.                                            |
| `app/services/reason_codes.py`                                            | Decides which reason codes the evidence supports. The script also imports its `graph_codes` for the grounding check. |
| `app/services/llm_service.py`, `app/prompts/investigator_prompt.py`       | Call Gemini with the investigator prompt.                                                               |
| `app/models/schemas.py`                                                   | Defines the request and response formats.                                                               |
| `app/config.py`                                                           | Reads settings from `.env`. The script uses it to get `SUPABASE_DB_URL`.                                |
