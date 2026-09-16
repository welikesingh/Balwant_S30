# Task 3 — Employee & Developer System Using Inheritance
# What to build
# Create a base class called Employee.
# It should contain employee ID, name, salary, and department, along with a method display_details().
# Now create a child class
# Employee
# |
# Developer
# Developer should inherit from Employee and contain additional information such as programming language and experience.
# Create at least 3 Employee/Developer objects and demonstrate how the child class can access functionality from 
# the parent class. Expected concepts: Parent class, child class, inheritance, object creation.

class employee:
    def __init__(self, employeeID, name, salary, department):
          self.employeeID = employeeID
          self.name = name
          self.salary = salary
          self.department = department

    def display_details(self):
         print(f"Employee: {self.employeeID}")
         print(f"Name: {self.name}")
         print(f"Salary: {self.salary}")
         print(f"Department: {self.department}")

class developer(employee):
    def __init__(self,employeeID, name, salary, department,programming_language, experiance):
            super().__init__(employeeID, name, salary, department) 
            self.programming_language = programming_language
            self.experiance = experiance 

    def display_details(self):
            super().display_details()
            print(f"Programming Details: {self.programming_language}")      
            print(f"Experiance: {self.experiance}")   


e1=employee(101,'Asha Rao', 55000, "HR")

d1=developer(201,"Ravi Kumar", 75000, "Engineering", "Python", 3)
d2=developer(202,"Meera Nair", 82000, "Engineering", "JavaScript", 5)


for person in [e1,d1,d2]:
    person.display_details()
    print("-"*40)
    