"""FastAPI Calculator API."""

import ast
import operator
from collections import deque

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Calculator API")

# --- In-memory history (last 20 calculations) ---
history: deque[dict] = deque(maxlen=20)


# --- Pydantic models ---
class OperationInput(BaseModel):
    a: float
    b: float


class CalculateInput(BaseModel):
    expression: str


class Result(BaseModel):
    result: float


class HistoryItem(BaseModel):
    operation: str
    details: str
    result: float


# --- Safe arithmetic expression parser (no eval) ---
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float:
    """Recursively evaluate a numeric expression from an AST."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPERATORS:
        return _SAFE_OPERATORS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPERATORS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _SAFE_OPERATORS[type(node.op)](left, right)
    raise ValueError(f"Unsupported expression element: {ast.unparse(node)}")


def safe_calculate(expr: str) -> float:
    """Evaluate a numeric expression safely via the AST."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise ValueError(f"Invalid expression: {expr}")
    return _safe_eval(tree.body)


def _record(operation: str, details: str, result: float) -> Result:
    history.append({"operation": operation, "details": details, "result": result})
    return Result(result=result)


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/add")
def add(body: OperationInput):
    return _record("add", f"{body.a} + {body.b}", body.a + body.b)


@app.post("/subtract")
def subtract(body: OperationInput):
    return _record("subtract", f"{body.a} - {body.b}", body.a - body.b)


@app.post("/multiply")
def multiply(body: OperationInput):
    return _record("multiply", f"{body.a} * {body.b}", body.a * body.b)


@app.post("/divide")
def divide(body: OperationInput):
    if body.b == 0:
        raise HTTPException(status_code=400, detail="Division by zero is not allowed")
    return _record("divide", f"{body.a} / {body.b}", body.a / body.b)


@app.post("/power")
def power(body: OperationInput):
    return _record("power", f"{body.a} ** {body.b}", body.a ** body.b)


@app.post("/calculate")
def calculate(body: CalculateInput):
    try:
        result = safe_calculate(body.expression)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Division by zero is not allowed")
    return _record("calculate", body.expression, result)


@app.get("/history")
def get_history():
    return list(history)
