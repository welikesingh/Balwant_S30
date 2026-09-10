
print("1.---Student Result Management System---")

print("""Create functions for
            accept student marks 
            calculate total
            calculate percentage
            assign grade
            determine pass/fail
            display result
            determine pass/fail
            display result
            Use loops wherever appropriate.""")

def accept_marks(num_subjects):
    """Accept marks for a given number of subjects using a loop."""
    marks = []
    

    for i in range(1, num_subjects + 1):
        while True:
            try:
                mark = float(input(f"Enter marks for subject {i} (0-100): "))
                if 0 <= mark <= 100:
                    marks.append(mark)
                    break
                print("Marks must be between 0 and 100.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    return marks


def calculate_total(marks):
    """Calculate the total sum of marks."""
    total = 0
    for mark in marks:
        total += mark
    return total


def calculate_percentage(total, num_subjects):
    """Calculate the percentage based on total and number of subjects."""
    return total / num_subjects


def determine_pass_fail(marks, passing_mark=40):
    """Determine if the student passed all subjects or failed any."""
    for mark in marks:
        if mark < passing_mark:
            return "FAIL"
    return "PASS"


def assign_grade(percentage, status):
    """Assign a letter grade based on percentage and pass/fail status."""
    if status == "FAIL":
        return "F"
    elif percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B"
    elif percentage >= 60:
        return "C"
    elif percentage >= 50:
        return "D"
    else:
        return "E"


def display_result(student_name, student_rno, marks, total, percentage, status, grade):
    """Display the final formatted result sheet."""
    print("\n--- Student Result Sheet ---")
    print(f"Student Name: {student_name}")
    print(f"Student Enrollment Number: {student_rno}")
    print(f"Marks obtained: {marks}")
    print(f"Total Marks: {total:.2f}")
    print(f"Percentage: {percentage:.2f}%")
    print(f"Status: {status}")
    print(f"Grade: {grade}")

while True :
    n = int(input("Enter the number of subjects: "))
    student_name = input("Enter Student Name: ")
    student_rno  = input("Enter Student Enrollment Number: ")
    student_marks = accept_marks(n)
    total_marks   = calculate_total(student_marks)
    percentage    = calculate_percentage(total_marks, n)
    pass_status   = determine_pass_fail(student_marks)
    final_grade   = assign_grade(percentage, pass_status)
    display_result(student_name, student_rno, student_marks, total_marks, percentage, pass_status, final_grade)    
    yes_no=input("Do you want to enter another student?(yes/no):")
    if yes_no.upper() in ('NO','N'):
      break;
