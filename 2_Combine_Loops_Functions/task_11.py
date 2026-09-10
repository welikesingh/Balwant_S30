
print('-----------------------------------------------------------------------------')
print("11.---Mini Authentication System---")
print(""" Create a small application supporting
            predefined username/password
            maximum login attempts
            successful login
            failed login
            logout
            retry logic
            Use functions and loops appropriately.
            """)

# Predefined login credentials
USERNAME = "admin"
PASSWORD = "admin123"

MAX_ATTEMPTS = 3


def login():
    attempts = 0
    while attempts < MAX_ATTEMPTS:
        username = input("Enter username: ")
        password = input("Enter password: ")
        # Check credentials
        if username == USERNAME and password == PASSWORD:
            print("\nLogin Successful!")
            return True
        else:
            attempts += 1
            remaining = MAX_ATTEMPTS - attempts
            print("\nLogin Failed!")
            if remaining > 0:
                print(f"You have {remaining} attempt(s) remaining.")
    print("\nMaximum login attempts reached.")
    return False


def logout():
    print("\nYou have been logged out successfully.")


def main_login_system():
    while True:
        print("\n===== LOGIN APPLICATION =====")
        print("1. Login")
        print("2. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            # Call login function
            successful_login = login()
            if successful_login:
                # User session
                while True:
                    print("\n===== USER MENU =====")
                    print("1. Logout")
                    print("2. Exit Application")
                    option = input("Enter your choice: ")
                    if option == "1":
                        logout()
                        break
                    elif option == "2":
                        print("Thank you for using the application!")
                        return
                    else:
                        print("Invalid option. Please try again.")
        elif choice == "2":
            print("Thank you for using the application!")
            break
        else:
            print("Invalid choice. Please try again.")

# Start the application
main_login_system()
