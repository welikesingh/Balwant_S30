"""
Calculator Program
A simple calculator that performs basic arithmetic operations.
"""


def add(a, b):
    """Add two numbers."""
    return a + b


def subtract(a, b):
    """Subtract second number from first number."""
    return a - b


def multiply(a, b):
    """Multiply two numbers."""
    return a * b


def divide(a, b):
    """Divide first number by second number."""
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b


def power(a, b):
    """Raise first number to the power of second number."""
    return a ** b


def modulo(a, b):
    """Get remainder of division."""
    if b == 0:
        raise ValueError("Cannot perform modulo by zero!")
    return a % b


def display_menu():
    """Display the calculator menu."""
    print("\n" + "=" * 40)
    print("           CALCULATOR MENU")
    print("=" * 40)
    print("  1. Addition (+)")
    print("  2. Subtraction (-)")
    print("  3. Multiplication (*)")
    print("  4. Division (/)")
    print("  5. Power (^)")
    print("  6. Modulo (%)")
    print("  7. Exit")
    print("=" * 40)


def get_number(prompt):
    """Get a valid number from user input."""
    while True:
        try:
            value = float(input(prompt))
            return value
        except ValueError:
            print("Invalid input! Please enter a valid number.")


def get_choice():
    """Get a valid menu choice from user."""
    while True:
        try:
            choice = int(input("\nEnter your choice (1-7): "))
            if 1 <= choice <= 7:
                return choice
            else:
                print("Invalid choice! Please enter a number between 1 and 7.")
        except ValueError:
            print("Invalid input! Please enter a number.")


def perform_operation(choice, num1, num2):
    """Perform the selected operation and return the result."""
    operations = {
        1: ("Addition", "+", add),
        2: ("Subtraction", "-", subtract),
        3: ("Multiplication", "*", multiply),
        4: ("Division", "/", divide),
        5: ("Power", "^", power),
        6: ("Modulo", "%", modulo),
    }
    
    operation_name, symbol, func = operations[choice]
    result = func(num1, num2)
    
    # Format result - show as integer if it's a whole number
    if result == int(result):
        result = int(result)
    
    print(f"\n>>> {num1} {symbol} {num2} = {result}")
    return result


def main():
    """Main function to run the calculator."""
    print("\n" + "*" * 40)
    print("*     Welcome to Python Calculator!    *")
    print("*" * 40)
    
    while True:
        display_menu()
        choice = get_choice()
        
        if choice == 7:
            print("\nThank you for using the calculator!")
            print("Goodbye! 👋")
            break
        
        # Get input numbers
        print("\n--- Enter Numbers ---")
        num1 = get_number("Enter first number: ")
        num2 = get_number("Enter second number: ")
        
        # Perform operation
        try:
            perform_operation(choice, num1, num2)
        except ValueError as e:
            print(f"\nError: {e}")
        
        # Ask if user wants to continue
        continue_choice = input("\nDo you want to perform another calculation? (y/n): ")
        if continue_choice.lower() != 'y':
            print("\nThank you for using the calculator!")
            print("Goodbye! 👋")
            break


if __name__ == "__main__":
    main()
