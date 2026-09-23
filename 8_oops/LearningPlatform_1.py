# ## Task 7 — Super30 Learning Platform
# What to build
# This is the main assignment combining everything covered so far.

# Build a mini Super30 Learning Platform.
# Students should design classes such as

# User
# |
# +---- Student
# |
# +---- Mentor

# The User class can contain name, email, and user ID.
# Student should contain course name and completed assignments.
# Mentor should contain expertise and number of students assigned.
# Students must use at least one class variable, one class method, one static method, 
# inheritance, multiple objects, constructors, and instance methods.

# Example functionality can include registering students, assigning a course, submitting an assignment, 
# displaying student information, displaying mentor information, and counting the total number of users.

class User:
    # Class variable
    total_users = 0

    # Constructor
    def __init__(self, name, email, user_id):
        if not User.is_valid_email(email):
          raise ValueError("Invalid Email on user initiation")
        self.name = name
        self.email = email
        self.user_id = user_id
        # Increase total users
        User.total_users += 1

    # Instance method
    def display_user_info(self):
        print(f"Name: {self.name}")
        print(f"Email: {self.email}")
        print(f"User ID: {self.user_id}")

    # Class method
    @classmethod
    def get_total_users(cls):
        return cls.total_users

    # Static method
    @staticmethod
    def is_valid_email(email):
        return "@" in email and "." in email

class Student(User):
    # Constructor
    def __init__(self, name, email, user_id, course_name):
        super().__init__(name, email, user_id)
        self.course_name = course_name
        self.completed_assignments = [] # initialize

    # Instance method
    def assign_course(self, course_name):
        self.course_name = course_name
        print(f"{self.name} assigned to {course_name}")

    # Instance method
    def submit_assignment(self, assignment):
        self.completed_assignments.append(assignment)
        print(f"{self.name} submitted: {assignment}")

    # Instance method
    def display_student_info(self):
        self.display_user_info()
        print(f"Course: {self.course_name}")
        print(f"Completed Assignments: {self.completed_assignments}")

class Mentor(User):
    # Constructor
    def __init__(self, name, email, user_id, expertise):
        super().__init__(name, email, user_id)
        self.expertise = expertise
        self.number_of_students = 0

    # Instance method
    def assign_student(self):
        self.number_of_students += 1
        print(f"Student assigned to mentor {self.name}")

    # Instance method
    def display_mentor_info(self):
        self.display_user_info()
        print(f"Expertise: {self.expertise}")
        print(f"Students Assigned: {self.number_of_students}")

# --------------------------------------------------------------------------
# Demonstration
# --------------------------------------------------------------------------
if __name__ == "__main__":
# -------------------------------
# Creating multiple objects
# -------------------------------
    student1 = Student("Balwant","balwant@gmail.com", 101,"Python")
    student2 = Student("Rahul","rahul@gmail.com",102,"Data Science")

    mentor1 = Mentor("Amit","amit@gmail.com",201,"Python and AI")

    print(" -- Assign courses -- ")
    student1.assign_course("Advanced Python")
    student2.assign_course("Machine Learning")
 
    print(" -- Submit assignments -- ")
    student1.submit_assignment("Assignment 1")
    student1.submit_assignment("Assignment 2")

    student2.submit_assignment("Assignment 1")

    print(" -- Assign students to mentor -- ")
    mentor1.assign_student()
    mentor1.assign_student()

    print(" -- Display information -- ")
    print("\n-- Student 1 Information --")
    student1.display_student_info()

    print("\n-- Student 2 Information --")
    student2.display_student_info()

    print("\n-- Mentor Information --")
    mentor1.display_mentor_info()

    # Class method
    print("\nTotal Users: ", User.get_total_users())

    # Static method
    print("\nEmail Validation: ")
    print(User.is_valid_email("test@gmail.com"))
    print(User.is_valid_email("invalid-email"))

                