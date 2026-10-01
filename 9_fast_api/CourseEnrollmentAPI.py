# Build a small FastAPI application where students can enroll in courses.
# POST /courses
# GET /courses
# POST /enroll
# GET /students/{student_id}/courses
# DELETE /enroll/{enrollment_id}
# Prevent a student from enrolling in the same course twice.
# Return meaningful errors such as 404 when a student/course doesn't exist.


# http://127.0.0.1:8000/docs
# uvicorn CourseEnrollmentAPI:app --reload --port 8000
# python -m pip install --upgrade fastapi pydantic uvicorn

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Course Enrollment API")

courses_list = []
enrollment_list = []

# -----------------------------
# Models
# -----------------------------
class Course(BaseModel):
    course_id: int = Field(ge=1, le=1000)
    course_name: str = Field(min_length=3, max_length=50)
    course_desc: str = Field(min_length=5, max_length=200)
    duration_days: int = Field(gt=0)

class Student(BaseModel):
    student_id: int = Field(ge=1, le=1000)
    student_name: str = Field(min_length=3, max_length=50)

class Enrollment(BaseModel):
    enrollment_id: int = Field(ge=1, le=1000)
    student_id: int = Field(ge=1, le=1000)
    course_id: int = Field(ge=1, le=1000)

# -----------------------------
# Pre-loaded students
# -----------------------------
students_list = [
    {"student_id": 1, "student_name": "Balwant"},
    {"student_id": 2, "student_name": "Amrendra"},
]

# -----------------------------
# Helper functions
# -----------------------------
def find_student(student_id: int):
    for student in students_list:
        if student["student_id"] == student_id:
            return student
    return None

def find_course(course_id: int):
    for course in courses_list:
        if course["course_id"] == course_id:
            return course
    return None

def find_enrollment(enrollment_id: int):
    for enrollment in enrollment_list:
        if enrollment["enrollment_id"] == enrollment_id:
            return enrollment
    return None
# ============================================================
# 1. POST /courses - Create a new course
# ============================================================
@app.post("/courses", status_code=201)
def create_course(course: Course):
    if find_course(course.course_id):
        raise HTTPException(
            status_code=409,
            detail=f"Course {course.course_id} already exists"
        )
    course_data = course.model_dump() if hasattr(course, "model_dump") else course.dict()
    courses_list.append(course_data)
    return {"message": "Course created successfully", "course": course_data}

# ============================================================
# 2. GET /courses - Get all courses
# ============================================================
@app.get("/courses")
def get_courses():
    return {"total": len(courses_list), "courses": courses_list}

# ============================================================
# 3. POST /enroll - Enroll a student into a course
# ============================================================
@app.post("/enroll", status_code=201)
def enroll_student(enrollment: Enrollment):
    # Student must exist
    if not find_student(enrollment.student_id):
        raise HTTPException(
            status_code=404,
            detail=f"Student {enrollment.student_id} not found"
        )
    # Course must exist
    if not find_course(enrollment.course_id):
        raise HTTPException(
            status_code=404,
            detail=f"Course {enrollment.course_id} not found"
        )
    # Enrollment ID must be unique
    if find_enrollment(enrollment.enrollment_id):
        raise HTTPException(
            status_code=409,
            detail=f"Enrollment ID {enrollment.enrollment_id} already exists"
        )
    # Prevent duplicate enrollment (same student, same course)
    for existing in enrollment_list:
        if (existing["student_id"] == enrollment.student_id
                and existing["course_id"] == enrollment.course_id):
            raise HTTPException(
                status_code=409,
                detail=(f"Student {enrollment.student_id} is already enrolled "
                        f"in course {enrollment.course_id}")
            )
    enrollment_data = {
        "enrollment_id": enrollment.enrollment_id,
        "student_id":    enrollment.student_id,
        "course_id":     enrollment.course_id,
        "enrollment_datetime": datetime.now().isoformat(timespec="seconds"),
    }
    enrollment_list.append(enrollment_data)
    return {"message": "Student enrolled successfully", "enrollment": enrollment_data}

# ============================================================
# 4. GET /students/{student_id}/courses - Courses for a student
# ============================================================
@app.get("/students/{student_id}/courses")
def get_student_courses(student_id: int):
    student = find_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=404,
            detail=f"Student {student_id} not found"
        )
    student_courses = []
    for enrollment in enrollment_list:
        if enrollment["student_id"] == student_id:
            course = find_course(enrollment["course_id"])
            if course:
                student_courses.append({
                    **course,
                    "enrollment_id": enrollment["enrollment_id"],
                    "enrollment_datetime": enrollment["enrollment_datetime"],
                })
    return {
        "student_id": student_id,
        "student_name": student["student_name"],
        "total_courses": len(student_courses),
        "courses": student_courses,
    }

# ============================================================
# 5. DELETE /enroll/{enrollment_id} - Delete an enrollment
# ============================================================
@app.delete("/enroll/{enrollment_id}")
def delete_enrollment(enrollment_id: int):
    enrollment = find_enrollment(enrollment_id)
    if enrollment is None:
        raise HTTPException(
            status_code=404,
            detail=f"Enrollment {enrollment_id} not found"
        )
    enrollment_list.remove(enrollment)
    return {"message": "Enrollment deleted successfully", "enrollment_id": enrollment_id}
