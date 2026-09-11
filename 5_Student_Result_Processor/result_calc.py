from exceptions import InvalidMarksError, MissingStudentInfoError

SUBJECTS = ["Maths", "Science", "English", "Social", "Computer"]
PASS_MARK = 40


def validate_marks(marks):
    if marks is None or len(marks) != 5:
        raise MissingStudentInfoError("Marks for all 5 subjects are required.")

    cleaned = []
    for i, mark in enumerate(marks):
        if mark is None or mark == "":
            raise MissingStudentInfoError(f"Marks missing for {SUBJECTS[i]}.")

        try:
            value = float(mark)
        except (TypeError, ValueError):
            raise InvalidMarksError(
                f"{SUBJECTS[i]} marks '{mark}' is not a number."
            )

        if value < 0 or value > 100:
            raise InvalidMarksError(
                f"{SUBJECTS[i]} marks {value} is outside 0-100."
            )

        cleaned.append(value)

    return cleaned


def calc_total(marks):
    return sum(marks)


def calc_percentage(total, no_of_subjects=5):
    try:
        return total / no_of_subjects
    except ZeroDivisionError:
        raise ZeroDivisionError("Cannot calculate percentage. Number of subjects is 0.")


def get_grade(percentage):
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    elif percentage >= PASS_MARK:
        return "E"
    else:
        return "F"


def get_pass_fail(marks, percentage):
    # fail if overall % is low or any subject is below pass mark
    if percentage < PASS_MARK:
        return "Fail"
    for m in marks:
        if m < PASS_MARK:
            return "Fail"
    return "Pass"


def process_result(student):
    name = student.get("name")
    roll = student.get("roll")
    marks = student.get("marks")

    if not name or str(name).strip() == "":
        raise MissingStudentInfoError("Student name is missing.")
    if not roll or str(roll).strip() == "":
        raise MissingStudentInfoError("Roll number is missing.")

    valid_marks = validate_marks(marks)
    total = calc_total(valid_marks)
    percentage = calc_percentage(total, len(valid_marks))
    grade = get_grade(percentage)
    status = get_pass_fail(valid_marks, percentage)

    student["marks"] = valid_marks
    student["total"] = total
    student["percentage"] = round(percentage, 2)
    student["grade"] = grade
    student["status"] = status
    student["processed"] = True
    return student
