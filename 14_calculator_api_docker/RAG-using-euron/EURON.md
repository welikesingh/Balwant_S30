# RAG-using-euron

FastAPI Calculator API with in-memory history and safe expression parsing.

Stack: Python 3.12, FastAPI, Pydantic v2, Streamlit, pytest, uvicorn

## Commands

### Install dependencies
```
pip install -r requirements.txt
```

### Run the API server
```
uvicorn app.main:app --reload
```
Then open **http://127.0.0.1:8000/docs** for the Swagger UI.

### Run the API in Docker
```
docker build -t calculator-api .
docker run -d --name calc-container -p 5000:8000 calculator-api
```
The API is available at **http://127.0.0.1:5000/docs**.

### Run the Streamlit calculator UI
The Streamlit app is a visual calculator that talks to the Docker API container.

**Step-by-step:**

1. **Start the API in Docker** (run this first — the UI needs it):
   ```
   docker run -d --name calc-container -p 5000:8000 calculator-api
   ```

2. **Install the frontend dependencies** (once):
   ```
   pip install -r streamlit-app/requirements.txt
   ```

3. **Start the Streamlit app:**
   ```
   streamlit run streamlit-app/app.py --server.port 8501
   ```

4. **Open your browser** at **http://127.0.0.1:8501** — the calculator UI appears, connected to the API on port 5000.

### Run the tests
```
python -m pytest tests/ -v
```

## Layout
```
app/
  __init__.py
  main.py            # FastAPI app: /health, /add, /subtract, /multiply,
                     # /divide, /power, /calculate (safe AST parser), /history
tests/
  test_main.py       # 26 pytest tests covering every endpoint
streamlit-app/
  requirements.txt   # streamlit, httpx
  app.py             # Streamlit calculator UI: display, digit buttons, history panel
requirements.txt
```

## Endpoints
| Method | Path          | Body                       | Returns          |
|--------|---------------|----------------------------|------------------|
| GET    | /health       | —                          | `{"status":"ok"}`|
| POST   | /add          | `{"a": <number>, "b": <number>}`  | `{"result": <float>}` |
| POST   | /subtract     | `{"a": <number>, "b": <number>}`  | `{"result": <float>}` |
| POST   | /multiply     | `{"a": <number>, "b": <number>}`  | `{"result": <float>}` |
| POST   | /divide       | `{"a": <number>, "b": <number>}`  | `{"result": <float>}` (400 if b=0) |
| POST   | /power        | `{"a": <number>, "b": <number>}`  | `{"result": <float>}` |
| POST   | /calculate    | `{"expression": "2 + 3 * 4"}`     | `{"result": <float>}` (safe AST parse) |
| GET    | /history      | —                          | Array of last 20 calculations |

## Conventions
- All numeric endpoints use Pydantic `OperationInput(a: float, b: float)` for validation.
- `/calculate` uses Python's `ast` module to parse expressions — no `eval()`.
- History is kept in a `deque(maxlen=20)` in memory.
- Tests use `starlette.testclient.TestClient` (synchronous, no network).
- The Streamlit UI calls the API at `http://localhost:5000`; start the Docker container first.
