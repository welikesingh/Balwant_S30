
print("8.---Password Strength Checker---")
print("""Create a function that checks whether a password contains
            uppercase
            lowercase
            number
            special character
            minimum 8 characters
            Return a meaningful strength/result.
     """)


def check_password(password):
    has_uppercase = False
    has_lowercase = False
    has_number = False
    has_special = False

    special_characters = "!@#$%^&*()-_+=[]{}|;:'\",.<>?/"

    # Check each character
    for char in password:
        if char.isupper():
            has_uppercase = True
        elif char.islower():
            has_lowercase = True
        elif char.isdigit():
            has_number = True
        elif char in special_characters:
            has_special = True

    # Check minimum length
    if len(password) < 8:
        return "Weak Password: Password must contain at least 8 characters."

    # Count how many conditions are satisfied
    conditions_met = sum([
        has_uppercase,
        has_lowercase,
        has_number,
        has_special
    ])

    if conditions_met == 4:
        return "Strong Password: All security requirements are satisfied."
    elif conditions_met == 3:
        return "Medium Password: One security requirement is missing."
    else:
        return "Weak Password: Multiple security requirements are missing."
