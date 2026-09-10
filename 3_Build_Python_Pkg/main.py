# This file uses the calculator_tools package.
# Run it from the project folder: python main.py

from calculator_tools.arithmetic import add, subtract, multiply, divide
from calculator_tools.statistics import percentage, average
from calculator_tools.converter import convert_temperature, convert_length
from calculator_tools.exceptions import InvalidOperationError


def main():
    print("=== Arithmetic ===")
    print("add(10, 5) =", add(10, 5))
    print("subtract(10, 5) =", subtract(10, 5))
    print("multiply(10, 5) =", multiply(10, 5))
    print("divide(10, 5) =", divide(10, 5))

    print()
    print("=== Percentage and average ===")
    print("percentage(25, 200) =", percentage(25, 200))
    print("average([10, 20, 30, 40]) =", average([10, 20, 30, 40]))

    print()
    print("=== Conversion ===")
    print("convert_temperature(100, 'C', 'F') =", convert_temperature(100, "C", "F"))
    print("convert_temperature(32, 'F', 'C') =", convert_temperature(32, "F", "C"))
    print("convert_length(1, 'km', 'm') =", convert_length(1, "km", "m"))
    print("convert_length(150, 'cm', 'm') =", convert_length(150, "cm", "m"))

    print()
    print("=== Error handling ===")

    try:
        print(divide(10, 0))
    except InvalidOperationError as error:
        print("divide(10, 0) ->", error)

    try:
        print(add("10", 5))
    except InvalidOperationError as error:
        print("add('10', 5) ->", error)

    try:
        print(average([]))
    except InvalidOperationError as error:
        print("average([]) ->", error)

    try:
        print(average([1, "two", 3]))
    except InvalidOperationError as error:
        print("average([1, 'two', 3]) ->", error)

    try:
        print(percentage(10, 0))
    except InvalidOperationError as error:
        print("percentage(10, 0) ->", error)

    try:
        print(convert_length(5, "km", "mile"))
    except InvalidOperationError as error:
        print("convert_length(5, 'km', 'mile') ->", error)


if __name__ == "__main__":
    main()
