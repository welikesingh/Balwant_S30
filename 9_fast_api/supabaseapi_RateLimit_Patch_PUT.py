from operator import ge, le
import os
from dotenv import load_dotenv
from supabase import create_client, Client
load_dotenv()
from fastapi import FastAPI

app = FastAPI()

SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
client = create_client(SUPABASE_URL, SUPABASE_KEY)


#### Implimenting GET request for retrieving all students ####
@app.get("/students")
def get_students():
    response = client.table("students_store").select("*").execute()
    return response.data

@app.get("/students/{student_id}")
def get_students_by_id(student_id: int):
    response = client.table("students_store").select("*").eq("id", student_id).execute()
    return response.data


@app.get("/students/age/{age}")
def filter_by_age(age: int):
    response = client.table("students_store").select("*").eq("age", age).execute()
    return response.data


#### Implimenting POST request for inserting a new student ####
from pydantic import BaseModel ,Field , EmailStr

class Student(BaseModel):
    name: str = Field(ge=5 , le=100)
    email : EmailStr
    age: int = Field(ge=18 , le=100)
    course: str


@app.post("/students/insert")
def insert_student(student: Student):
    response = client.table("students_store").insert(student.dict()).execute()
    return response.data

#### Implimenting PUT request for updating student information ####
class studentupdate(BaseModel):
    name: str = Field(min_length=5 , max_length=100)
    email : EmailStr
    age: int = Field(ge=18 , le=100)
    course: str

@app.put("/students/update/{student_id}")
def update_student(student_id: int, student: studentupdate):
    response = client.table("students_store").update(student.dict()).eq("id", student_id).execute()
    return response.data

#### Implimenting PATCH request for updating student information ####
#### note here is defined seprate class for PATCH request to allow partial updates
class studentpatch(BaseModel):
    name: str | None = Field(default=None, min_length=5 , max_length=100)
    email : EmailStr | None = Field(default=None)
    age: int | None = Field(default=None, ge=18 , le=100)
    course: str | None = Field(default=None)

## exclude_unset=True ensures that only fields that have been 
## explicitly set in the PATCH request are included in the update.
@app.patch("/students/patch/{student_id}")
def student_patch(student_id: int, student: studentpatch):
    response = client.table("students_store").update(student.dict(exclude_unset=True)).eq("id", student_id).execute()
    return response.data

#### Implimenting DELETE request for removing a student ####
@app.delete("/students/delete/{student_id}")
def delete_student(student_id: int):
    response = client.table("students_store").delete().eq("id", student_id).execute()
    return response.data


##########Rate Limiting Configuration##########
# a client can make only a limited number of requests within a specific time window.
# For this example, we'll allow each client to make 5 requests per minute to the student endpoints. 
# If the client exceeds the limit, the API returns HTTP 429 — Too Many Requests.

from slowapi import Limiter
from fastapi import Request
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/studentslimit/xyz")
@limiter.limit("5/minute")
def limit_student_update(request:Request):
    response = client.table("students_store").select("*").execute()
    return response.data
