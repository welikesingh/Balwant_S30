# Create a FastAPI application for managing students.
# Required APIs
# POST /students
# GET /students
# GET /students/{student_id}
# PUT /students/{student_id}
# DELETE /students/{student_id}
# Student fields can include id, name, email, age, and course. 
# Use Pydantic validation and return appropriate HTTP status codes.

# http://127.0.0.1:8001/docs
# uvicorn StudentCRUDAPI:app --reload --port 8001
# python -m pip install --upgrade fastapi pydantic uvicorn


from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

app = FastAPI()

# ==========================================
# Student Model
# ==========================================
class Student(BaseModel):
    student_id: int = Field(gt=0, le=10000)
    name: str = Field(min_length=3, max_length=50)
    email: EmailStr
    age: int = Field(ge=5, le=100)
    course: str = Field(min_length=2, max_length=50)

# ==========================================
# In-memory database
# ==========================================
students_list = []

# ==========================================
# 1. POST /students
# Create a new student
# ==========================================
@app.post("/students", status_code=status.HTTP_201_CREATED)
def create_student(student: Student):
    # Check whether student already exists
    for existing_student in students_list:
        if existing_student["student_id"] == student.student_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student {student.student_id} already exists"
            )
    # Convert Pydantic model to dictionary
    student_data = student.model_dump()
    students_list.append(student_data)
    return {
        "message": "Student created successfully",
        "student": student_data
    }

# ==========================================
# 2. GET /students
# Get all students
# ==========================================
@app.get("/students")
def get_students():
    return {
        "students": students_list
    }

# ==========================================
# 3. GET /students/{student_id}
# Get one student
# ==========================================
@app.get("/students/{student_id}")
def get_student(student_id: int):
    for student in students_list:
        if student["student_id"] == student_id:
            return student
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Student {student_id} not found"
    )

# ==========================================
# 4. PUT /students/{student_id}
# Update an existing student
# ==========================================
@app.put("/students/{student_id}")
def update_student(student_id: int, updated_student: Student):
    for index, student in enumerate(students_list):
        if student["student_id"] == student_id:
            # Make sure ID in URL and body are same
            if updated_student.student_id != student_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student ID in URL and request body must match"
                )
            students_list[index] = updated_student.model_dump()
            return {
                "message": "Student updated successfully",
                "student": students_list[index]
            }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Student {student_id} not found"
    )

# ==========================================
# 5. DELETE /students/{student_id}
# Delete a student
# ==========================================
@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    for index, student in enumerate(students_list):
        if student["student_id"] == student_id:
            deleted_student = students_list.pop(index)
            return {
                "message": "Student deleted successfully",
                "student": deleted_student
            }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Student {student_id} not found"
    )


