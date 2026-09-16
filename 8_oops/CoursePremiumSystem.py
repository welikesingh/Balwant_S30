### Task 5 — Course & Premium Course System

# What to build
# Build a simple online learning platform using inheritance.
# Use this structure
# Course
# |
# PremiumCourse
# The Course class should contain course name, instructor, duration, and price.
# Add methods such as

# show_course_details()
# calculate_discount()

# PremiumCourse should inherit from Course and add attributes such as mentor support and live sessions.

# Use a class variable to count how many courses have been created and a class method to return the course count.

# This task should demonstrate how a real EdTech platform can model courses using OOP.


class Course:
        course_count=0  # class variable: shared across Course AND PremiumCourse
        def __init__(self,course_name,instructor,duration,price):
                self.course_name = course_name
                self.instructor  = instructor
                self.duration    = duration
                self.price       = price
                Course.course_count = Course.course_count + 1
                
        def show_course_details(self):
                print(f"Course Name: {self.course_name}")
                print(f"Instructor: {self.instructor}")
                print(f"Duration: {self.duration}")
                print(f"Price: {self.price}")
                print(f"Course Count: {Course.course_count}")

        def calculate_discount(self) -> float:
                """Standard courses get a flat 5% discount."""
                return self.price * 0.05

        @classmethod
        def get_course_count(cls) -> int:
                return(cls.course_count)              


class PremiumCourse(Course):
    def __init__(self, course_name, instructor, duration, price,
                 mentor_support: bool, live_sessions: int):
        super().__init__(course_name, instructor, duration, price)
        self.mentor_support = mentor_support
        self.live_sessions = live_sessions

    def show_course_details(self):
        super().show_course_details()
        print(f"Mentor Support : {'Yes' if self.mentor_support else 'No'}")
        print(f"Live Sessions  : {self.live_sessions}")

    def calculate_discount(self) -> float:
        """Premium courses get 10% instead of the base 5%."""
        return self.price * 0.10

# --- demonstration ---
c1 = Course("Python Basics","Anjali Sharma","4 weeks",1000)

c2 = Course("SQL Fundamentals", "Rahul Verma", "3 weeks", 800)

p1 = PremiumCourse("Full Stack Web Dev", "Priya Nair", "12 weeks", 15000,
                    mentor_support=True, live_sessions=20)

p2 = PremiumCourse("Data Science Masterclass", "Karthik Iyer", "16 weeks", 20000,
                    mentor_support=True, live_sessions=30)

courses = [c1, c2, p1, p2]

for course in courses:
    course.show_course_details()
    print(f"Discount: {course.calculate_discount()}")
    print("-" * 30)

print("Total courses created:", Course.get_course_count())  # 4

