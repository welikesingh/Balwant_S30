from auth import login, logout
from logger_config import setup_logging
from exception_handler import handle_critical_error
from file_operations import read_file, write_file
from calculator import calculate

MENU_OPTIONS = {"0", "1", "2", "3", "4", "5"}

def show_menu():
    """Display the application menu."""
    print("\n1. Login")
    print("2. Calculate")
    print("3. Read a File")
    print("4. Write a File")
    print("5. Logout")
    print("0. Exit")

def run_activity(choice, logger):
    """Run an activity for a logged-in user."""
    if   choice == "2":
        calculate(logger)
    elif choice == "3":
        read_file(logger)
    elif choice == "4":
        write_file(logger)

def main():
    """Run the menu until the user exits the application."""
    logger = setup_logging()
    logged_in = False
    logger.debug("Application started")
    while True:
        try:
            show_menu()
            choice = input("Enter your choice: ").strip()
            if choice == "0":
                logger.info("Application closed")
                print("Goodbye! Logout.")
                break
            if choice not in MENU_OPTIONS:
                logger.warning("Invalid menu choice: %s", choice)
                print("Invalid choice. Please enter a number from 0 to 5.")
            elif choice == "1":
                if logged_in:
                    print("You are already logged in.")
                else:
                    logged_in = login(logger)
            elif not logged_in:
                logger.warning("User tried to use the menu without logging in")
                print("Please log in first.")
            elif choice == "5":
                logout(logger)
                logged_in = False
            else:
                run_activity(choice, logger)                    
        except (KeyboardInterrupt, EOFError):
            logger.info("Application stopped by user")
            print("\nGoodbye!")
            break
        except Exception:
            handle_critical_error(logger)

if __name__ == "__main__":
    main()
