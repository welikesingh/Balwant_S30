from exception_handler import handle_error


def perform_calculation(first_number, operator, second_number):
    """Return the result of a basic arithmetic calculation."""
    if operator == "+":
        return first_number + second_number
    if operator == "-":
        return first_number - second_number
    if operator == "*":
        return first_number * second_number
    if operator == "/":
        return first_number / second_number
    raise ValueError("The operation must be +, -, *, or /.")


def calculate(logger):
    """Collect calculation details and display the answer."""
    try:
        first_number = float(input("Enter first number: "))
        operator = input("Enter operation (+, -, *, /): ").strip()
        second_number = float(input("Enter second number: "))
        answer = perform_calculation(first_number, operator, second_number)
        print("Answer:", answer)
        logger.info("Calculation completed successfully")
    except ValueError as error:
        handle_error(logger, error, str(error))
    except ZeroDivisionError as error:
        handle_error(logger, error, "A number cannot be divided by zero.")
