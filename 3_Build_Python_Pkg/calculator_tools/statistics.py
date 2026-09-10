from .exceptions import InvalidOperationError


def check_number(value, name):
    if type(value) == int or type(value) == float:
        return value
    raise InvalidOperationError(name + " must be a number")


def percentage(part, whole):
    # Example: 25 out of 200 is 12.5 percent
    part = check_number(part, "part")
    whole = check_number(whole, "whole")
    if whole == 0:
        raise InvalidOperationError("Cannot calculate percentage when whole is zero")
    return (part / whole) * 100


def average(numbers):
    if type(numbers) != list:
        raise InvalidOperationError("average needs a list of numbers")
    if len(numbers) == 0:
        raise InvalidOperationError("Cannot calculate average of an empty list")

    total = 0
    for number in numbers:
        if type(number) != int and type(number) != float:
            raise InvalidOperationError("Every item in the list must be a number")
        total = total + number

    return total / len(numbers)
