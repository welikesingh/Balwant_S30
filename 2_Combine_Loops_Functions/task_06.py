
print('6.--Employee Salary Analyzer--')
print(""" Given employee salaries, 
            create functions to determine
                total payroll
                average salary
                highest salary
                lowest salary
                employees earning above average""")

# storing in dictionary as employee and salary
emp_salaries = {
    "Emp1": 75000,
    "Emp2": 50000,
    "Charlie": 110000,
    "David": 45000,
    "Eva": 85000
}


def drive_board_values(employee_sal):
    # Extract names and salaries
    employees = list(employee_sal.keys())
    
    # Initialize tracking variables using the first employee
    first_emp = employees[0]
    highest_salary = employee_sal[first_emp]
    highest_emp = first_emp
    
    lowest_salary = employee_sal[first_emp]
    lowest_emp = first_emp
    
    total_payroll = 0
    total_employees = 0

    # First pass: Calculate total, highest, and lowest
    for emp, salary in employee_sal.items():
        total_payroll += salary
        total_employees += 1
        
        if salary > highest_salary:
            highest_salary = salary
            highest_emp = emp
            
        if salary < lowest_salary:
            lowest_salary = salary
            lowest_emp = emp

    # Calculate average
    average_salary = total_payroll / total_employees

    # Second pass: Find employees earning strictly above average
    above_average_employees = []
    for emp, salary in employee_sal.items():
        if salary > average_salary:
            above_average_employees.append(emp)

    # Format above average list as a readable string
    above_avg_str = ", ".join(above_average_employees) if above_average_employees else "None"

    # Return results separated by newlines
    return (
        f"Total Payroll: ${total_payroll:,.2f}\n"
        f"Average Salary: ${average_salary:,.2f}\n"
        f"Highest Salary: {highest_emp} (${highest_salary:,.2f})\n"
        f"Lowest Salary: {lowest_emp} (${lowest_salary:,.2f})\n"
        f"Employees Earning Above Average: {above_avg_str}"
    )

print(drive_board_values(emp_salaries))
