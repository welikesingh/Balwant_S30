## Class definition
class Student:
    total_students = 0  # class variable: shared across all instances

    def __init__(self, name: str, email: str, student_id: str, course: str, marks=None):
        self.name = name
        self.email = email
        self.student_id = student_id
        self.course = course
        self.marks = marks if marks is not None else []  # avoid mutable default arg bug
        Student.total_students += 1  # increment shared counter on every new student


    ########## Instance Methods##########
    def add_mark(self, mark: float):
        """Add a single new mark (e.g., after a new test)."""
        if not (0 <= mark <= 100):
            raise ValueError("Mark must be between 0 and 100")
        self.marks.append(mark)

    def update_marks(self, new_marks: list):
        """Replace the entire marks list (e.g., correcting a full record)."""
        for m in new_marks:
            if not (0 <= m <= 100):
                raise ValueError(f"Invalid mark: {m}")
        self.marks = new_marks

    def calculate_average(self) -> float:
        if not self.marks:
            return 0.0
        return sum(self.marks) / len(self.marks)

    def display_details(self):
        print("-" * 30)
        print(f"Name       : {self.name}")
        print(f"Email      : {self.email}")
        print(f"Student ID : {self.student_id}")
        print(f"Course     : {self.course}")
        print(f"Marks      : {self.marks}")
        print(f"Average    : {self.calculate_average():.2f}")
        print("-" * 30)

    ########## Class Methods##########
    @classmethod
    def get_total_students(cls) -> int:
        return cls.total_students




# --- quick test ---
s1 = Student("Alice", "alice@mail.com", "S001", "Computer Science", [85, 90, 78])
s2 = Student("Bob", "bob@mail.com", "S002", "Mathematics")

s1.display_details()

s2.add_mark(60)
s2.add_mark(75)

s2.display_details()

s1.update_marks([95, 92, 88, 91])
print("Alice's new average:", s1.calculate_average())

print("Total students:", Student.get_total_students())

s1.display_details()