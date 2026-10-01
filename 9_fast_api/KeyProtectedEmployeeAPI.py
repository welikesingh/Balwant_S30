# Create an Employee Management API where certain endpoints are protected 
# using an API key.
# Example
# GET /employees
# POST /employees
# PUT /employees/{employee_id}
# DELETE /employees/{employee_id}
# For protected endpoints, expect a header such as
# X-API-Key: super30-secret-key
# If the API key is missing or incorrect, return an appropriate 401/403 response.
# Add Pydantic validation for employee data.

# Protected endpoints expect the header:  X-API-Key: super30-secret-key
# Missing key -> 401, wrong key -> 403
# http://127.0.0.1:8000/docs  (click "Authorize" and paste the key)
# uvicorn KeyProtectedEmployeeAPI:app --reload --port 8000

# In /docs, click the Authorize button at the top right, 
# paste super30-secret-key, and the protected endpoints (POST/PUT/DELETE) opration will send the key automatically.
# it is because they have defined with dependencies=[Depends(verify_api_key)

# Hardcoding the key is fine for this exercise. In a real project 
# you'd read it from an environment variable, like os.getenv("API_KEY").

# Optional[str] → The value can be a string or None.
# APIKeyHeader → Tells FastAPI to read the API key from an HTTP header.
# Security() → Tells FastAPI to use a security dependency to obtain/validate authentication information.

   
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

app = FastAPI(title="Employee Management API")

API_KEY = "super30-secret-key"
API_KEY_NAME = "X-API-Key"

# auto_error=False lets us return our own 401/403 messages
# APIKeyHeader is a FastAPI security utility used to read an API key from a specific HTTP request header
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# -----------------------------
# API key check (dependency)
# -----------------------------
# Security is a function used to declare security-related dependencies, such as API keys, OAuth2, 
# or other authentication mechanisms.
# What does Optional[str] mean?
# In modern Python, you can also write:
# api_key: str | None
# or 
# api_key: Optional[str]
# Meaning of syntax
#api_key       : Optional[str] = Security(api_key_header)
#     ↓                ↓                 ↓
#parameter          type          where FastAPI gets it

def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail=f"API key missing. Send it in the '{API_KEY_NAME}' header.",
            headers={"WWW-Authenticate": "API-Key"},
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )
    return api_key

# -----------------------------
# Models
# -----------------------------
class Employee(BaseModel):
    employee_id: int = Field(ge=1, le=10000)
    name: str = Field(min_length=3, max_length=50)
    email: str = Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
    department: str = Field(min_length=2, max_length=30)
    salary: float = Field(gt=0, le=10_000_000)
    age: int = Field(ge=18, le=65)
    joining_date: date

class EmployeeUpdate(BaseModel):
    # All fields optional: send only what you want to change
    name: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[str] = Field(default=None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
    department: Optional[str] = Field(default=None, min_length=2, max_length=30)
    salary: Optional[float] = Field(default=None, gt=0, le=10_000_000)
    age: Optional[int] = Field(default=None, ge=18, le=65)
    joining_date: Optional[date] = None

# -----------------------------
# In-memory storage
# -----------------------------
employees_list = [
    {
        "employee_id": 1,
        "name": "Balwant",
        "email": "balwant@example.com",
        "department": "Engineering",
        "salary": 90000.0,
        "age": 30,
        "joining_date": "2024-01-15",
    },
    {
        "employee_id": 2,
        "name": "Amrendra",
        "email": "amrendra@example.com",
        "department": "HR",
        "salary": 60000.0,
        "age": 28,
        "joining_date": "2025-03-01",
    },
]

def find_employee(employee_id: int):
    for emp in employees_list:
        if emp["employee_id"] == employee_id:
            return emp
    return None

# ============================================================
# 1. GET /employees - Public
# ============================================================
@app.get("/employees")
def get_employees():
    return {"total": len(employees_list), "employees": employees_list}

# ============================================================
# 2. POST /employees - Protected
# ============================================================
@app.post("/employees", status_code=201, dependencies=[Depends(verify_api_key)])
def create_employee(employee: Employee):
    if find_employee(employee.employee_id):
        raise HTTPException(
            status_code=409,
            detail=f"Employee {employee.employee_id} already exists",
        )
    for emp in employees_list:
        if emp["email"].lower() == employee.email.lower():
            raise HTTPException(
                status_code=409,
                detail=f"Email {employee.email} is already in use",
            )
    employee_data = employee.model_dump(mode="json")
    employees_list.append(employee_data)
    return {"message": "Employee created successfully", "employee": employee_data}

# ============================================================
# 3. PUT /employees/{employee_id} - Protected
# ============================================================
@app.put("/employees/{employee_id}", dependencies=[Depends(verify_api_key)])
def update_employee(employee_id: int, employee: EmployeeUpdate):
    existing = find_employee(employee_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"Employee {employee_id} not found",
        )
    updates = employee.model_dump(mode="json", exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    if "email" in updates:
        for emp in employees_list:
            if (emp["employee_id"] != employee_id
                    and emp["email"].lower() == updates["email"].lower()):
                raise HTTPException(
                    status_code=409,
                    detail=f"Email {updates['email']} is already in use",
                )
    existing.update(updates)
    return {"message": "Employee updated successfully", "employee": existing}

# ============================================================
# 4. DELETE /employees/{employee_id} - Protected
# ============================================================
@app.delete("/employees/{employee_id}", dependencies=[Depends(verify_api_key)])
def delete_employee(employee_id: int):
    existing = find_employee(employee_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"Employee {employee_id} not found",
        )
    employees_list.remove(existing)
    return {"message": "Employee deleted successfully", "employee_id": employee_id}
