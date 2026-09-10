print("12.---Super30 Python Utility Application---")
print("""Menu-driven application with:
            Calculator
            Palindrome checker
            Prime checker
            Factorial calculator
            Multiplication table
            Number analyzer
            Password checker
""")


def read_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a number.")


def read_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a whole number.")


def calculator():
    print("\n--- Calculator ---")
    print("Operations: +  -  *  /  %")
    num1 = read_float("Enter first number: ")
    operator = input("Enter operator: ").strip()
    num2 = read_float("Enter second number: ")

    if operator == "+":
        result = num1 + num2
    elif operator == "-":
        result = num1 - num2
    elif operator == "*":
        result = num1 * num2
    elif operator == "/":
        if num2 == 0:
            print("Cannot divide by zero.")
            return
        result = num1 / num2
    elif operator == "%":
        if num2 == 0:
            print("Cannot modulo by zero.")
            return
        result = num1 % num2
    else:
        print("Unknown operator. Use +, -, *, /, or %.")
        return

    print(f"Result: {num1} {operator} {num2} = {result}")


def palindrome_checker():
    print("\n--- Palindrome Checker ---")
    text = input("Enter a word, phrase, or number: ")
    cleaned = ""
    for char in text.lower():
        if char.isalnum():
            cleaned += char

    if not cleaned:
        print("Nothing to check after removing spaces and punctuation.")
        return

    reversed_text = ""
    for char in cleaned:
        reversed_text = char + reversed_text

    if cleaned == reversed_text:
        print(f"'{text}' is a palindrome.")
    else:
        print(f"'{text}' is not a palindrome.")


def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def prime_checker():
    print("\n--- Prime Checker ---")
    number = read_int("Enter a whole number: ")
    if is_prime(number):
        print(f"{number} is a prime number.")
    else:
        print(f"{number} is not a prime number.")


def factorial_calculator():
    print("\n--- Factorial Calculator ---")
    number = read_int("Enter a non-negative whole number: ")
    if number < 0:
        print("Factorial is not defined for negative numbers.")
        return

    result = 1
    for i in range(1, number + 1):
        result *= i
    print(f"{number}! = {result}")


def multiplication_table():
    print("\n--- Multiplication Table ---")
    number = read_int("Enter a number: ")
    up_to = read_int("Show table up to (e.g. 10): ")
    if up_to < 1:
        print("Upper limit must be at least 1.")
        return

    print(f"\nMultiplication table of {number}:")
    for i in range(1, up_to + 1):
        print(f"{number} x {i} = {number * i}")


def number_analyzer():
    print("\n--- Number Analyzer ---")
    print("Enter numbers separated by spaces (example: 4 -2 9 0 3)")
    raw = input("Numbers: ").strip()
    if not raw:
        print("No numbers entered.")
        return

    numbers = []
    for part in raw.split():
        try:
            numbers.append(float(part))
        except ValueError:
            print(f"Skipping invalid value: {part}")

    if not numbers:
        print("No valid numbers to analyze.")
        return

    largest = numbers[0]
    smallest = numbers[0]
    total = 0
    even_count = 0
    odd_count = 0
    positive_count = 0
    negative_count = 0

    for num in numbers:
        total += num
        if num > largest:
            largest = num
        if num < smallest:
            smallest = num
        if num > 0:
            positive_count += 1
        elif num < 0:
            negative_count += 1
        if num == int(num):
            if int(num) % 2 == 0:
                even_count += 1
            else:
                odd_count += 1

    average = total / len(numbers)
    print("\nAnalysis:")
    print(f"Count: {len(numbers)}")
    print(f"Largest: {largest}")
    print(f"Smallest: {smallest}")
    print(f"Total: {total}")
    print(f"Average: {average:.2f}")
    print(f"Even count: {even_count}")
    print(f"Odd count: {odd_count}")
    print(f"Positive count: {positive_count}")
    print(f"Negative count: {negative_count}")


def password_checker():
    print("\n--- Password Checker ---")
    password = input("Enter a password to check: ")

    has_uppercase = False
    has_lowercase = False
    has_number = False
    has_special = False
    special_characters = "!@#$%^&*()-_+=[]{}|;:'\",.<>?/"

    for char in password:
        if char.isupper():
            has_uppercase = True
        elif char.islower():
            has_lowercase = True
        elif char.isdigit():
            has_number = True
        elif char in special_characters:
            has_special = True

    print("\nRequirements:")
    print(f"  At least 8 characters : {'Yes' if len(password) >= 8 else 'No'}")
    print(f"  Uppercase letter      : {'Yes' if has_uppercase else 'No'}")
    print(f"  Lowercase letter      : {'Yes' if has_lowercase else 'No'}")
    print(f"  Number                : {'Yes' if has_number else 'No'}")
    print(f"  Special character     : {'Yes' if has_special else 'No'}")

    if len(password) < 8:
        print("\nResult: Weak Password (must contain at least 8 characters).")
        return

    conditions_met = 0
    for flag in (has_uppercase, has_lowercase, has_number, has_special):
        if flag:
            conditions_met += 1

    if conditions_met == 4:
        print("\nResult: Strong Password.")
    elif conditions_met == 3:
        print("\nResult: Medium Password (one requirement missing).")
    else:
        print("\nResult: Weak Password (multiple requirements missing).")


def display_menu():
    print("\n===== PYTHON UTILITY MENU =====")
    print("1. Calculator")
    print("2. Palindrome Checker")
    print("3. Prime Checker")
    print("4. Factorial Calculator")
    print("5. Multiplication Table")
    print("6. Number Analyzer")
    print("7. Password Checker")
    print("8. Exit")


def utility_app():
    while True:
        display_menu()
        choice = input("Enter your choice (1-8): ").strip()

        if choice == "1":
            calculator()
        elif choice == "2":
            palindrome_checker()
        elif choice == "3":
            prime_checker()
        elif choice == "4":
            factorial_calculator()
        elif choice == "5":
            multiplication_table()
        elif choice == "6":
            number_analyzer()
        elif choice == "7":
            password_checker()
        elif choice == "8":
            print("Thank you for using the Python Utility Application!")
            break
        else:
            print("Invalid choice. Please select a number from 1 to 8.")


if __name__ == "__main__":
    utility_app()
