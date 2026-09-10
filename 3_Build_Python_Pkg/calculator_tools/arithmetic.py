from .exceptions import InvalidOperationError


def check_number(value, name):
    if type(value) == int or type(value) == float:
        return value
    raise InvalidOperationError(name + " must be a number")


def add(a, b):
    a = check_number(a, "a")
    b = check_number(b, "b")
    return a + b


def subtract(a, b):
    a = check_number(a, "a")
    b = check_number(b, "b")
    return a - b


def multiply(a, b):
    a = check_number(a, "a")
    b = check_number(b, "b")
    return a * b


def divide(a, b):
    a = check_number(a, "a")
    b = check_number(b, "b")
    if b == 0:
        raise InvalidOperationError("Cannot divide by zero")
    return a / b
