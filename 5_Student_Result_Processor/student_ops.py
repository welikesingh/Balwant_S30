import json
import os

from exceptions import StudentNotFoundError, MissingStudentInfoError
from result_calc import SUBJECTS

DATA_FILE = "students.json"


def load_students():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_students(students):
    with open(DATA_FILE, "w") as f:
        json.dump(students, f, indent=2)


def find_index(students, roll):
    roll = str(roll).strip()
    for i, s in enumerate(students):
        if str(s.get("roll", "")).strip() == roll:
            return i
    return -1


def add_student(students, name, roll, marks):
    name = str(name).strip() if name is not None else ""
    roll = str(roll).strip() if roll is not None else ""

    if not name or not roll:
        raise MissingStudentInfoError("Name and roll number cannot be empty.")

    if find_index(students, roll) != -1:
        raise MissingStudentInfoError(f"Roll number {roll} already exists.")

    student = {
        "name": name,
        "roll": roll,
        "marks": marks,
        "total": None,
        "percentage": None,
        "grade": None,
        "status": None,
        "processed": False,
    }
    students.append(student)
    save_students(students)
    return student


def search_student(students, roll):
    idx = find_index(students, roll)
    if idx == -1:
        raise StudentNotFoundError(f"No student found with roll number {roll}.")
    return students[idx]


def delete_student(students, roll):
    idx = find_index(students, roll)
    if idx == -1:
        raise StudentNotFoundError(f"No student found with roll number {roll}.")
    removed = students.pop(idx)
    save_students(students)
    return removed


def update_student(students, roll, name=None, marks=None):
    idx = find_index(students, roll)
    if idx == -1:
        raise StudentNotFoundError(f"No student found with roll number {roll}.")

    student = students[idx]
    if name is not None and str(name).strip() != "":
        student["name"] = str(name).strip()
    if marks is not None:
        student["marks"] = marks

    # result needs to be calculated again after an update
    student["total"] = None
    student["percentage"] = None
    student["grade"] = None
    student["status"] = None
    student["processed"] = False

    save_students(students)
    return student


def show_student(student):
    print("-" * 40)
    print(f"Name       : {student.get('name')}")
    print(f"Roll No    : {student.get('roll')}")
    marks = student.get("marks") or []
    for i, sub in enumerate(SUBJECTS):
        mark = marks[i] if i < len(marks) else "-"
        print(f"{sub:<10} : {mark}")
    if student.get("processed"):
        print(f"Total      : {student.get('total')}")
        print(f"Percentage : {student.get('percentage')}%")
        print(f"Grade      : {student.get('grade')}")
        print(f"Result     : {student.get('status')}")
    else:
        print("Result     : Not processed yet")
    print("-" * 40)
