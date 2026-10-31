# Vector Search Internals — beginner project

This is a simplified teaching rewrite of the supplied notebook, with explicit loops, named variables, visible rankings, and optional external services. The original is not modified.

## Files
- `vector_search_beginner.ipynb`: executable, annotated Python walkthrough.
- `vector_search_presentation.html`: standalone browser presentation with math, rankings, and an interactive 2D comparison.
- `requirements.txt`: Python packages.
- `.env.example`: optional Gemini and Qdrant connection settings.

## Run (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set GEMINI_API_KEY if using real Gemini vectors.
docker run -d --name vector-demo -p 6333:6333 qdrant/qdrant
jupyter notebook vector_search_beginner.ipynb
```
Run notebook cells in order. You can use the 2D and NumPy sections without Gemini or Docker. Missing Gemini key gives **labelled synthetic demonstration vectors**. Missing Qdrant skips comparisons; it does not silently substitute an in-memory database. For benchmarks, start Qdrant and set `RUN_BENCHMARK = True` in the last code cell. Benchmarking 10,000 x 3,072 vectors uses substantial RAM and index build time.

## Expected hand calculations
|Point|Euclidean distance to (2,4)|Cosine similarity|
|---|---:|---:|
|A=(2,3)|1.0000|0.9923|
|B=(1,2)|2.2361|1.0000|
|C=(0,4)|2.0000|0.8944|

**Euclidean ranking:** A, C, B. **Cosine ranking:** B, A, C. B is collinear with q, but A is closer in space.

## What HNSW changes
A full scan computes a similarity or distance against every stored vector, roughly O(N × dimensions) per query. HNSW (Hierarchical Navigable Small World) builds a layered graph connecting nearby vectors. Search starts at sparse upper layers and follows promising neighbors to finer layers, comparing only a subset of vectors. It often scales better for large collections, but uses extra memory, takes time to build/update, and can miss some true nearest neighbors. The query-time `hnsw_ef` parameter controls a speed-versus-recall tradeoff. `m` and `ef_construct` affect graph structure and construction quality. HNSW does **not** change the definition of cosine or Euclidean distance.

**Benchmark interpretation:** the notebook measures NumPy computation time and Qdrant *end-to-end client round-trip* time, so networking and serialization affect comparisons. Its recall@10 checks how many true top-10 neighbors Qdrant returns. If `HNSW indexed=False`, do not present the timing as an indexed-HNSW result. Results are machine-dependent and are not included until you run them. Synthetic data is used for 1,000 and 10,000 vectors to avoid Gemini API costs; this measures retrieval performance, not embedding generation time.

## Key formula
- Euclidean: `sqrt(sum((x - q)^2))`; lower is better.
- Cosine: `dot(x,q)/(norm(x)*norm(q))`; higher is better.
- Normalize: `x_unit = x/norm(x)`; then `cosine(x,q) = dot(x_unit,q_unit)`.
- On unit vectors: `euclidean(x_unit,q_unit)^2 = 2 - 2*cosine(x,q)`.

The Gemini API requires a key, internet access, and available model access. Qdrant requires a running server for the comparison and benchmark sections.
