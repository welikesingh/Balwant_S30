# Create an Employee Management System in Python. 
# Create an Employee class with employee ID, name, department, salary, and designation. 

# Add methods to display employee information, update salary, and calculate annual salary. 
# Create at least 5 employee objects.




class Employee:
  """Represents an employee with basic HR details and salary operations."""
  #constructor
  def __init__(self,employee_ID, name, department, salary, designation):
        self.employee_ID= employee_ID
        self.name = name
        self.department = department
        self.salary = salary
        self.designation = designation
   #Instance method
  def update_salary(self, new_salary):
      if new_salary < 0:
            print(f"Invalid salary update for {self.name}: salary cannot be negative.")
            return
      self.salary=new_salary


  def calculate_annual_salary(self):
       return 12*self.salary


  def display_employee(self):
       print(f"Employee_ID: {self.employee_ID}")
       print(f"Name: {self.name}")
       print(f"Department: {self.department}")
       print(f"Monthly Salary: ${self.salary:.2f}")
       print(f"Annual Salary : ${self.calculate_annual_salary():.2f}")
       print(f"Designation: {self.designation}")


if __name__ == "__main__":
    # Create at least 5 employee objects
    employees = [
        Employee(101, "Aditi Sharma", "Engineering", 8500, "Software Engineer"),
        Employee(102, "Rohan Mehta", "Sales", 6200, "Sales Executive"),
        Employee(103, "Sara Khan", "Marketing", 7000, "Marketing Manager"),
        Employee(104, "David Lee", "Finance", 9200, "Financial Analyst"),
        Employee(105, "Priya Nair", "Human Resources", 6800, "HR Coordinator"),
    ]

    # Display all employee information
    print("===== Employee Records =====\n")
    for emp in employees:
        emp.display_employee()
        print("_"*30)

    # Demonstrate updating a salary
    print("\n===== Salary Update =====\n")
    employees[0].update_salary(9500)   # give Aditi a raise
    employees[3].update_salary(9800)   # give David a raise

    # Show updated info for those two employees
    print("\n===== Updated Records =====\n")
    employees[0].display_employee()
    print("_"*30)
    employees[3].display_employee()
