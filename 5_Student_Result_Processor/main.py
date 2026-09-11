from exceptions import InvalidMarksError, MissingStudentInfoError, StudentNotFoundError
from logger_config import setup_logger
from result_calc import SUBJECTS, process_result
from student_ops import (
    add_student,
    delete_student,
    load_students,
    save_students,
    search_student,
    show_student,
    update_student,
)

logger = setup_logger()


def show_menu():
    print("\n=== Student Result Management System ===")
    print("1. Add new student")
    print("2. Process students")
    print("3. Search student")
    print("4. Delete a student record")
    print("5. Update student record")
    print("6. Exit")


def read_marks():
    marks = []
    print("Enter marks for 5 subjects (0 to 100):")
    for sub in SUBJECTS:
        value = input(f"  {sub}: ").strip()
        marks.append(value)
    return marks


def option_add(students):
    print("\n--- Add New Student ---")
    name = input("Student name: ").strip()
    roll = input("Roll number: ").strip()
    marks = read_marks()

    try:
        student = add_student(students, name, roll, marks)
        print(f"Student {student['name']} added. Use option 2 to calculate result.")
    except MissingStudentInfoError as e:
        logger.error(f"Could not add student: {e}")
        print("Could not add student:", e)
    except Exception as e:
        logger.error(f"Unexpected error while adding student: {e}")
        print("Something went wrong while adding the student.")


def option_process(students):
    print("\n--- Process Students ---")
    if not students:
        print("No student records found.")
        return

    ok = 0
    failed = 0

    for student in students:
        roll = student.get("roll", "?")
        name = student.get("name", "?")
        try:
            process_result(student)
            print(f"Processed {name} (Roll {roll}) -> {student['status']}, Grade {student['grade']}")
            ok += 1
        except (InvalidMarksError, MissingStudentInfoError, ZeroDivisionError, TypeError, ValueError) as e:
            logger.error(f"Error processing roll {roll} ({name}): {e}")
            print(f"Skipped {name} (Roll {roll}): {e}")
            student["processed"] = False
            failed += 1
        except Exception as e:
            logger.error(f"Unexpected error for roll {roll} ({name}): {e}")
            print(f"Skipped {name} (Roll {roll}) due to an unexpected error.")
            student["processed"] = False
            failed += 1

    save_students(students)
    print(f"\nDone. Processed: {ok}, Skipped: {failed}")
    print("Check logs/student_system.log for error details.")


def option_search(students):
    print("\n--- Search Student ---")
    roll = input("Enter roll number: ").strip()
    try:
        student = search_student(students, roll)
        show_student(student)
    except StudentNotFoundError as e:
        logger.error(str(e))
        print(e)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        print("Could not search right now.")


def option_delete(students):
    print("\n--- Delete Student ---")
    roll = input("Enter roll number to delete: ").strip()
    try:
        removed = delete_student(students, roll)
        print(f"Deleted record of {removed['name']} (Roll {removed['roll']}).")
    except StudentNotFoundError as e:
        logger.error(str(e))
        print(e)
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        print("Could not delete the record.")


def option_update(students):
    print("\n--- Update Student ---")
    roll = input("Enter roll number to update: ").strip()
    try:
        student = search_student(students, roll)
        show_student(student)

        print("Leave blank if you do not want to change that field.")
        new_name = input("New name: ").strip()
        change_marks = input("Update marks? (y/n): ").strip().lower()

        marks = None
        if change_marks == "y":
            marks = read_marks()

        if new_name == "":
            new_name = None

        if new_name is None and marks is None:
            print("Nothing to update.")
            return

        updated = update_student(students, roll, name=new_name, marks=marks)
        print(f"Updated {updated['name']}. Run Process students to refresh the result.")
    except StudentNotFoundError as e:
        logger.error(str(e))
        print(e)
    except Exception as e:
        logger.error(f"Update failed: {e}")
        print("Could not update the record.")


def main():
    students = load_students()
    print("Welcome. Student records are saved in students.json")

    while True:
        show_menu()
        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            option_add(students)
        elif choice == "2":
            option_process(students)
        elif choice == "3":
            option_search(students)
        elif choice == "4":
            option_delete(students)
        elif choice == "5":
            option_update(students)
        elif choice == "6":
            save_students(students)
            print("Bye.")
            break
        else:
            print("Please enter a number from 1 to 6.")


if __name__ == "__main__":
    main()
