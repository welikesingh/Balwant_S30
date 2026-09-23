# Design a small learning platform using inheritance. 
# Create a parent User class and child classes such as Student, Mentor, and Admin. 
# Implement common properties in the parent and role-specific functionality in the child classes. 
# Demonstrate method overriding.


# Polymorphism is the concept to observe behaviour: means you  call  a method on objects of different types 
# and each one responds in its own way, without the caller needing to know which exact type it's dealing with.

# Method overriding is one specific technique used to achieve polymorphism: a subclass redefines a method that 
# already exists in its parent class, giving it new behavior while keeping the same name and signature.

# overriding is the mechanism; polymorphism is the result/behavior you get from using it.


# way to remember it:
# Overriding = how you write the code (redefining a method in a subclass).
# Polymorphism = what you observe when you run the code (same call, different behavior depending on the object).


class User:
    # class variable
    users_count=0
    # Constructor
    def __init__(self, name, email, user_id):
        if not User.is_email_valid(email):
           raise ValueError("Invalid Email on user initiation")
        self.name=name
        self.email=email
        self.user_id =user_id
        #Class variable
        User.users_count +=1

    #class method
    @classmethod
    def get_total_users(cls):
        return cls.users_count
    #static method  
    @staticmethod
    def is_email_valid(email):
        return "@" in email and "." in email  
    
    def get_role(self):
        """Default role label. Overridden by each subclass."""
        return "User"
    
    # Instance method
    def display_info(self):
        print(f"Name: {self.name}")
        print(f"Email: {self.email}")
        print(f"User ID: {self.user_id}")

class Student(User):
    # Constructor
    def __init__(self, name, email, user_id):
        super().__init__(name, email, user_id)
        self.enrolled_courses = [] # initialize
        self.completed_courses = [] # initialize

    def get_role(self):  # Overridding
        return "Student"

    def enroll(self, course_name: str):
        self.enrolled_courses.append(course_name)
        print(f"{self.name} enrolled in '{course_name}'.")

    def complete_course(self, course_name: str):
        if course_name in self.enrolled_courses:
            self.enrolled_courses.remove(course_name)
            self.completed_courses.append(course_name)
            print(f"{self.name} completed '{course_name}'.")

    # Instance method
    def display_info(self):
        self.display_info()
        print(f"Course Enrolled: {self.enrolled_courses or 'None'}")


class Mentor(User):
    def __init__(self, name, email, user_id,expertiseSkill):
        super().__init__(name, email, user_id)
        self.expertiseSkill = expertiseSkill
        self.assigned_students = []

    def assign_student(self, Student):
        self.assigned_students.append(Student)
        print(f"{Student.name} has been assigned to mentor {self.name}.")

    def give_feedback(self, student: Student, feedback: str) -> None:
        print(f"Mentor {self.name} ->feedback for-> {student.name}: \"{feedback}\"")

    def get_role(self):  # Overridding
        return "Mentor"
    
    # Instance method
    def display_info(self):
        self.display_info()
        print(f"Mentor Skill: {self.expertiseSkill}")
        print(f"Mentor: {self.user} Assigned Mentor Student for student: {self.assigned_students or 'None'} ")


class Admin(User):
    def __init__(self, name, email, user_id ):
        super().__init__(name, email, user_id)
        self.users_managed=[] # initialize

    # Instance method
    def display_info(self):
        self.display_info()
        print(f"Assigned Student for Mentor: {self.users_managed or 'None'} ")    

    def add_user(self, user: User):
        self.users_managed.append(user)
        print(f"Admin {self.name} added {user.get_role()} '{user.name}' ")

    def get_role(self):  # Overridding
        return "Admin"
    
    def remove_user(self, user: User):
        if user in self.users_managed:
           self.users_managed.remove(user)
           print(f"Admin {self.name} removed {user.get_role()} '{user.name}' ")


if __name__ == "__main__":
    admin = Admin("John", "John@platform.com",1)
    mentor = Mentor("Raj", "raj@platform.com", 2, expertiseSkill="Data Science")
    student = Student("Anu", "anu@platform.com",3 )

    admin.add_user(mentor)
    admin.add_user(student)

    mentor.assign_student(student)
    student.enroll("Python Basics")
    student.complete_course("Python Basics")
    mentor.give_feedback(student, "Great progress on Python Basics!")


# plymorphism behaviour
for user in [admin, mentor, student]:
    print(user.get_role()) 