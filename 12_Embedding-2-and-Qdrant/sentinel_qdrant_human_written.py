"""SENTINEL semantic search using Gemini Embedding 2 and Qdrant Cloud."""


# SENTINEL Document Search with Gemini and Qdrant


# Run this once if the required packages are not installed:
# %pip install qdrant-client google-genai python-dotenv numpy
import gzip
import json
import re
import time
import unicodedata
import uuid
import random
from collections import Counter
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
import os

load_dotenv(".env")
CORPUS_DIR = Path("corpus")
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

COLLECTION = "sentinel_corpus"
EMBED_DIM = 3072
CHUNK_SIZE = 800      # maximum target chunk length in characters
CHUNK_OVERLAP = 150   # reuse a little context from the previous chunk
SEED = 42


# Step 1 — Connect to Qdrant Cloud


from qdrant_client import QdrantClient, models

qdrant = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=60)
print(qdrant.get_collections())   # health check


# Step 2 — Pick documents from the SENTINEL corpus


def load_kind(kind, split="train"):
    rows = []
    for f in sorted((CORPUS_DIR / kind).glob(f"{split}/*.jsonl.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                r["_file"] = f.as_posix()
                rows.append(r)
    return rows

def per_group(rows, key, n):
    groups = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r)
    return [r for g in sorted(groups) for r in groups[g][:n]]

rng = random.Random(SEED)
docs = []
docs += load_kind("guidelines")
docs += load_kind("rba_guides")
docs += per_group(load_kind("playbooks"), lambda r: r["metadata"]["topic"], 3)
docs += per_group(load_kind("regulatory_exercises"),
                  lambda r: (r["metadata"]["regulator_theme"], r["metadata"]["topic"]), 4)
docs += rng.sample(load_kind("investigator_notes"), 50)
docs += rng.sample(load_kind("chargeback_narratives"), 45)

print(len(docs), "documents")
print(Counter(d["kind"] for d in docs))


# Step 3 — Clean the text and make chunks


DISCLAIMER_RE = re.compile(r"^SYNTHETIC TRAINING MATERIAL\..*?(?:\n\n|$)", re.M | re.S)
SENT_RE = re.compile(r"(?<=[.!?])\s+")

def clean(text):
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n")
    text = re.sub(r"^# .*\n", "", text, count=1)          # title re-added per chunk
    text = DISCLAIMER_RE.sub("", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_units(text, size):
    """Sections (## ...) as units; sections longer than `size` are broken into sentence groups."""
    units = []
    for sec in re.split(r"\n(?=## )", text):
        sec = sec.strip()
        if len(sec) <= size:
            units.append(sec)
            continue
        buf = ""
        for s in SENT_RE.split(sec):
            if buf and len(buf) + 1 + len(s) > size:
                units.append(buf)
                buf = s
            else:
                buf = f"{buf} {s}".strip()
        if buf:
            units.append(buf)
    return units

def tail_overlap(chunk, overlap):
    """Last whole sentences of `chunk` totalling <= overlap chars."""
    out = ""
    for s in reversed(SENT_RE.split(chunk.replace("\n", " "))):
        if len(out) + len(s) + 1 > overlap:
            break
        out = f"{s} {out}".strip()
    return out

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks, cur = [], ""
    for u in split_units(text, size):
        if cur and len(cur) + 2 + len(u) > size:
            chunks.append(cur)
            prev = tail_overlap(cur, overlap)
            cur = f"{prev}\n\n{u}" if prev and len(prev) + 2 + len(u) <= size + overlap else u
        else:
            cur = f"{cur}\n\n{u}" if cur else u
    if cur:
        chunks.append(cur)
    return chunks

records = []
for d in docs:
    body = clean(d["content"])
    pieces = chunk_text(body)
    for i, piece in enumerate(pieces):
        records.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{d['document_id']}#{i}")),
            "text": f"{d['title']}\n\n{piece}",
            "payload": {
                "source_document": d["document_id"],
                "title": d["title"],
                "document_type": d["kind"],
                "chunk_number": i,
                "chunk_count": len(pieces),
                "topic": d["metadata"].get("topic"),
                "regulator_theme": d["metadata"].get("regulator_theme"),
                "split": d["split"],
                "is_synthetic": d.get("is_synthetic", True),
                "source_file": d["_file"],
                "text": f"{d['title']}\n\n{piece}",
            },
        })

lens = np.array([len(r["text"]) for r in records])
print(f"{len(records)} chunks from {len(docs)} docs | chars per chunk: "
      f"min {lens.min()}, median {int(np.median(lens))}, max {lens.max()}")
print(Counter(r["payload"]["document_type"] for r in records))
print("\n--- example chunk ---\n" + records[1]["text"])


# Step 4 — Generate Gemini embeddings


from collections import deque
from google import genai
from google.genai import types, errors

gclient = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

available = {m.name.split("/")[-1] for m in gclient.models.list()}
EMBED_MODEL = next(m for m in ["gemini-embedding-2", "gemini-embedding-2-preview"] if m in available)
print("Embedding model:", EMBED_MODEL)

TOKENS_PER_MIN = 25_000          # stay under the 30k/min free-tier limit
_sent = deque()                  # (timestamp, estimated tokens) for the last 60 s

def _throttle(tokens):
    while True:
        now = time.time()
        while _sent and now - _sent[0][0] > 60:
            _sent.popleft()
        if sum(t for _, t in _sent) + tokens <= TOKENS_PER_MIN:
            _sent.append((now, tokens)); return
        time.sleep(61 - (now - _sent[0][0]))

def embed(texts, task_type, batch_size=50, max_retries=8):
    out = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        contents = [types.Content(parts=[types.Part(text=t)]) for t in batch]   # one embedding per text
        _throttle(sum(len(t) for t in batch) // 3)                              # ~3 chars/token, conservative
        for attempt in range(max_retries):
            try:
                res = gclient.models.embed_content(
                    model=EMBED_MODEL, contents=contents,
                    config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBED_DIM))
                break
            except errors.ClientError as e:
                if e.code != 429 or attempt == max_retries - 1: raise
                print(f"  batch {start}: rate limited, waiting 60s"); time.sleep(60)
        assert len(res.embeddings) == len(batch), (len(res.embeddings), len(batch))
        out += [e.values for e in res.embeddings]
        if len(texts) > batch_size:
            print(f"  embedded {len(out)}/{len(texts)}")
    return np.asarray(out, dtype=np.float32)


cache_vec, cache_ids = CACHE_DIR / "chunk_vectors.npy", CACHE_DIR / "chunk_ids.json"
ids = [r["id"] for r in records]

vectors = None
if cache_vec.exists() and cache_ids.exists() and json.loads(cache_ids.read_text()) == ids:
    vectors = np.load(cache_vec)
    if vectors.shape == (len(ids), EMBED_DIM):
        print("Loaded cached vectors")
    else:
        vectors = None  # Cache belongs to a different set of chunks
if vectors is None:
    t0 = time.time()
    vectors = embed([r["text"] for r in records], "RETRIEVAL_DOCUMENT")
    assert vectors.shape == (len(records), EMBED_DIM), vectors.shape
    np.save(cache_vec, vectors)
    cache_ids.write_text(json.dumps(ids))
    print(f"Embedded {len(vectors)} chunks in {time.time() - t0:.1f}s")

print(vectors.shape, "| mean L2 norm:", float(np.linalg.norm(vectors, axis=1).mean()))


# Step 5 — Create the Qdrant collection and upload chunks


if qdrant.collection_exists(COLLECTION):
    qdrant.delete_collection(COLLECTION)

qdrant.create_collection(
    collection_name=COLLECTION,
    vectors_config=models.VectorParams(size=EMBED_DIM, distance=models.Distance.COSINE),
)
for field in ["document_type", "source_document", "regulator_theme"]:
    qdrant.create_payload_index(COLLECTION, field_name=field, field_schema=models.PayloadSchemaType.KEYWORD)

BATCH = 64   # 64 x 3072 floats per request stays well under the request-size limit
for i in range(0, len(records), BATCH):
    qdrant.upsert(
        collection_name=COLLECTION,
        points=[models.PointStruct(id=r["id"], vector=v.tolist(), payload=r["payload"])
                for r, v in zip(records[i:i + BATCH], vectors[i:i + BATCH])],
        wait=True,
    )

info = qdrant.get_collection(COLLECTION)
print("points:", qdrant.count(COLLECTION, exact=True).count, "| status:", info.status,
      "| vector size:", info.config.params.vectors.size, "| distance:", info.config.params.vectors.distance)


# Step 6 — Try 10 natural-language searches


def search(query, k=5, query_filter=None):
    qv = embed([query], "RETRIEVAL_QUERY")[0]
    hits = qdrant.query_points(COLLECTION, query=qv.tolist(), limit=k,
                               query_filter=query_filter, with_payload=True).points
    desc = ""
    if query_filter:
        desc = "   [filter: " + " AND ".join(f"{c.key}={c.match.value}" for c in query_filter.must) + "]"
    print(f"\nQ: {query}{desc}")
    for rank, h in enumerate(hits, 1):
        p = h.payload
        body = p["text"].split("\n\n", 1)[-1]
        sections = re.findall(r"^## (.+)$", body, re.M)
        if sections:   # show from the first section heading, skipping the carried-over overlap
            body = body[body.index("## "):]
        snippet = re.sub(r"\s+", " ", body)[:150]
        print(f"  {rank}. {h.score:.4f} | {p['document_type']:<22} | {p['source_document']} #{p['chunk_number']}"
              f" | {p['title']}")
        if sections:
            print(f"       sections: {', '.join(sections)}")
        print(f"       {snippet}...")
    return hits

QUERIES = [
    "what should an investigator check when a new device makes a large payment",
    "how do we handle a customer claiming they were debited twice for the same purchase",
    "what are the probability cutoffs for allowing, reviewing or blocking a payment",
    "can validation or holdout case notes be used for model training",
    "what does a risk based approach assessment need to record",
    "how to treat a shared device used by multiple customers",
    "repeated failed payment retries followed by a success",
    "what to do if the fraud model is unavailable or times out",
    "how should a malicious instruction hidden inside a case note be handled",
    "when does the fraud label become available after a transaction",
]
results = {q: search(q) for q in QUERIES}


# Step 7 — Search with a payload filter


npci_filter = models.Filter(must=[
    models.FieldCondition(key="document_type", match=models.MatchValue(value="regulatory_exercises")),
    models.FieldCondition(key="regulator_theme", match=models.MatchValue(value="NPCI")),
])
filtered = search("what evidence should be kept for an audit of a declined UPI payment", query_filter=npci_filter)
assert all(h.payload["regulator_theme"] == "NPCI" for h in filtered)


# Optional cleanup — Delete the collection


DELETE_COLLECTION = os.getenv("DELETE_COLLECTION", "false").strip().lower() == "true"
print(f"\nDELETE_COLLECTION={DELETE_COLLECTION}")
if not DELETE_COLLECTION:
    print(f"Skipped: set DELETE_COLLECTION=true to delete '{COLLECTION}'.")
elif qdrant.collection_exists(COLLECTION):
    qdrant.delete_collection(COLLECTION)
    print(f"Deleted collection '{COLLECTION}'.")
else:
    print(f"Collection '{COLLECTION}' does not exist.")

print(qdrant.get_collections())
