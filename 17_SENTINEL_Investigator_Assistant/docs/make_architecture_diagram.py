"""Draws docs/architecture.png.   uv run python docs/make_architecture_diagram.py"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).with_name("architecture.png")

INK, MUTED = "#1f2933", "#52606d"
COLORS = {
    "api": ("#e8f0fe", "#3b6fd8"), "sql": ("#e6f6ee", "#2f9e6a"), "graph": ("#eef1ff", "#4a63c9"),
    "vector": ("#fdf1e6", "#d9822b"), "llm": ("#f3ecfb", "#8a5cc7"), "out": ("#f1f3f5", "#52606d"),
}

fig, ax = plt.subplots(figsize=(16, 10), dpi=150)
ax.set_xlim(0, 160)
ax.set_ylim(0, 100)
ax.axis("off")
fig.patch.set_facecolor("white")


def box(x, y, w, h, kind, title, lines, size=9.2):
    fill, edge = COLORS[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.5",
                                linewidth=1.8, edgecolor=edge, facecolor=fill))
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="top", fontsize=12, fontweight="bold", color=INK)
    ax.text(x + w / 2, y + h - 7.2, "\n".join(lines), ha="center", va="top", fontsize=size,
            color=MUTED, linespacing=1.5)


def arrow(start, end, color, label="", label_xy=None, both=False, ha="center"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="<|-|>" if both else "-|>", mutation_scale=15,
                                 linewidth=1.7, color=color, shrinkA=1, shrinkB=1))
    if label:
        x, y = label_xy or ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 1.2)
        ax.text(x, y, label, ha=ha, va="bottom", fontsize=8.4, color=color, style="italic", linespacing=1.3)


ax.text(80, 98, "SENTINEL Fraud Investigator Assistant — Hybrid Graph RAG", ha="center", va="top",
        fontsize=18, fontweight="bold", color=INK)
ax.text(80, 93.8, "One POST /explain call combines structured, graph and semantic evidence into a grounded, "
        "validated JSON explanation", ha="center", va="top", fontsize=10.5, color=MUTED)

# Left column: client and output
box(2, 68, 25, 17, "out", "Client", ["Investigator / curl / Swagger", "POST /explain", '{"transaction_id": "TX_..."}'])
box(2, 14, 25, 44, "out", "JSON response", [
    "recommended_action", "ALLOW | MANUAL_REVIEW | ESCALATE", "",
    "database_facts  (written by code)", "llm_interpretation  (by LLM)",
    "reason_codes + DB evidence", "citations  (retrieved chunks only)",
    "missing_information", "evidence_status, validation", "disclaimer: not a calibrated score"], size=7.9)

# Orchestrator
box(37, 30, 46, 55, "api", "FastAPI  ·  Orchestrator", [
    "app/services/investigation.py", "",
    "1  Supabase: transaction + features",
    "    (critical: 404 / 503 if missing)",
    "2  Neo4j: neighborhood before the",
    "    payment time, matured labels only",
    "3  build policy query from codes",
    "    -> embed -> top-5 Qdrant chunks",
    "4  consolidate evidence; derive",
    "    SUPPORTED reason codes (rules)",
    "5  grounded prompt -> Gemini LLM",
    "6  validate: schema, codes, citations,",
    "    action guardrails"], size=9.3)

arrow((27, 77), (37, 77), MUTED, "request", (32, 78))
arrow((37, 40), (27, 40), MUTED, "validated\nJSON", (32, 41))

# Databases
box(97, 71, 33, 17, "sql", "Supabase PostgreSQL", [
    "transactions · features FE-01..10", "reason_codes R01-R08", "hard_rules · list_entries",
    "(labels table never read)"], size=8.8)
box(97, 44, 33, 22, "graph", "Neo4j", [
    "(Customer)-[:USED_DEVICE]->(Device)", "(Customer)-[:PAID]->(Merchant)",
    "PAID: tx id, amount, time, label,", "label_available_at, split",
    "shared devices · fraud links · merchant"], size=8.8)
box(97, 12, 33, 26, "vector", "Qdrant Cloud", [
    "collection sentinel_corpus2", "850 chunks · 3072-d · cosine",
    "playbooks · RBI/NPCI exercises", "guidelines · RBA guide",
    "payload: source_document,", "chunk_number, title, topic"], size=8.8)
box(136, 12, 22, 26, "vector", "Gemini Emb. 2", [
    "gemini-embedding-2", "RETRIEVAL_QUERY", "3072 dims", "matches ingestion", "(RETRIEVAL_DOCUMENT)"],
    size=8.6)

arrow((83, 79), (97, 79), COLORS["sql"][1], "SQL by tx id\ntransaction facts", (90, 80), both=True)
arrow((83, 55), (97, 55), COLORS["graph"][1], "Cypher, cutoff\ngraph evidence", (90, 56), both=True)
arrow((83, 34), (97, 26), COLORS["vector"][1], "policy query\ntop-5 chunks", (89, 31.5), both=True)
arrow((130, 25), (136, 25), COLORS["vector"][1], both=True)
ax.text(133, 26.2, "vector", ha="center", va="bottom", fontsize=8, color=COLORS["vector"][1], style="italic")

# LLM
box(37, 2, 46, 20, "llm", "Gemini LLM", [
    "gemini-3.8-flash  (fallback 3.5-flash-lite)", "JSON schema output · temperature 0",
    "policy text = untrusted data", "no fraud label · no credentials"], size=8.8)
arrow((52, 30), (52, 22), COLORS["llm"][1], "evidence", (49, 25.2), ha="right")
arrow((68, 22), (68, 30), COLORS["llm"][1], "LLMExplanation", (71, 25.2), ha="left")

# Why three databases
ax.text(134, 88, "Why three databases?", fontsize=11.5, fontweight="bold", color=INK, va="top")
ax.text(134, 84, "Supabase — exact facts and\nengineered features for the\ntransaction being explained.\n\n"
        "Neo4j — relationships that tables\nhide: shared devices, links to\nconfirmed fraud, merchant history.\n\n"
        "Qdrant — semantic search over\npolicies so each explanation\ncan cite a real chunk.",
        fontsize=8.8, color=MUTED, va="top", linespacing=1.4)

ax.text(80, -1.5, "Guardrails: Pydantic schema · codes must be supported by DB evidence · citations must match "
        "retrieved metadata · blocklisted device -> ESCALATE · incomplete evidence never ALLOW · "
        "the assistant never blocks a payment", ha="center", va="top", fontsize=8.8, color=MUTED)

fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print(f"Saved {OUT}")
