from .exceptions import InvalidOperationError


def check_number(value, name):
    if type(value) == int or type(value) == float:
        return value
    raise InvalidOperationError(name + " must be a number")


def celsius_to_fahrenheit(celsius):
    celsius = check_number(celsius, "celsius")
    return (celsius * 9 / 5) + 32


def fahrenheit_to_celsius(fahrenheit):
    fahrenheit = check_number(fahrenheit, "fahrenheit")
    return (fahrenheit - 32) * 5 / 9


def convert_temperature(value, from_unit, to_unit):
    value = check_number(value, "value")

    if type(from_unit) != str or type(to_unit) != str:
        raise InvalidOperationError("Units must be text like C or F")

    from_unit = from_unit.upper()
    to_unit = to_unit.upper()

    # First change the input into Celsius
    if from_unit == "C":
        celsius = value
    elif from_unit == "F":
        celsius = fahrenheit_to_celsius(value)
    elif from_unit == "K":
        if value < 0:
            raise InvalidOperationError("Kelvin cannot be less than 0")
        celsius = value - 273.15
    else:
        raise InvalidOperationError("Unsupported temperature unit. Use C, F, or K")

    # Then change Celsius into the requested unit
    if to_unit == "C":
        return celsius
    elif to_unit == "F":
        return celsius_to_fahrenheit(celsius)
    elif to_unit == "K":
        kelvin = celsius + 273.15
        if kelvin < 0:
            raise InvalidOperationError("Temperature is below absolute zero")
        return kelvin
    else:
        raise InvalidOperationError("Unsupported temperature unit. Use C, F, or K")


def convert_length(value, from_unit, to_unit):
    value = check_number(value, "value")

    if type(from_unit) != str or type(to_unit) != str:
        raise InvalidOperationError("Units must be text like m or km")

    from_unit = from_unit.lower()
    to_unit = to_unit.lower()

    # First change the input into meters
    if from_unit == "m":
        meters = value
    elif from_unit == "km":
        meters = value * 1000
    elif from_unit == "cm":
        meters = value / 100
    else:
        raise InvalidOperationError("Unsupported length unit. Use cm, m, or km")

    # Then change meters into the requested unit
    if to_unit == "m":
        return meters
    elif to_unit == "km":
        return meters / 1000
    elif to_unit == "cm":
        return meters * 100
    else:
        raise InvalidOperationError("Unsupported length unit. Use cm, m, or km")
