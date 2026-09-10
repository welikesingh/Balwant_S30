"""Main menu for running each task script without editing the task files."""

# app.py now starts each file with subprocess — the same as running python task_01.py yourself. 
# Task files stay unchanged, each run is a fresh process, and after a task exits you return to the menu.


import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

# Menu number -> (script filename, label)
TASKS = {
        "1": ("task_01.py", "Student Result Management System"),
        "2": ("task_02.py", "Banking Application"),
        "3": ("task_03.py", "Inventory Management"),
        "4": ("task_04.py", "Quiz Application"),
        "5": ("task_05.py", "Number Analysis Tool"),
        "6": ("task_06.py", "Employee Salary Analyzer"),
        "7": ("task_07.py", "Shopping Cart"),
        "8": ("task_08.py", "Password Strength Checker"),
        "9": ("task_09.py", "Prime Number Analyzer"),
        "10": ("task_10.py", "Expense Tracker"),
        "11": ("task_11.py", "Mini Authentication System"),
        "12": ("task_12_utility_app.py", "Python Utility Application"),
        }

EXIT_CHOICE = "13"


def print_menu():
    print("\n==============================")
    print("     UTILITY APPLICATION")
    print("==============================")
    for number, (_, title) in TASKS.items():
        print(f"{number}. {title}")
    print(f"{EXIT_CHOICE}. Exit")


def run_task(script_name):
    """Run a task file as its own program (same as: python task_XX.py)."""
    script_path = APP_DIR / script_name
    if not script_path.exists():
        print(f"File not found: {script_path}")
        return

    print()
    result = subprocess.run([sys.executable, str(script_path)], cwd=APP_DIR)

    if result.returncode != 0:
        print(f"\n{script_name} ended with an error (exit code {result.returncode}).")
    else:
        print(f"\n--- Returned to main menu from {script_name} ---")


def main_app():
    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == EXIT_CHOICE:
            print("Thank you for using the application!")
            break

        task = TASKS.get(choice)
        if task is None:
            print(f"Invalid choice. Please select a number from 1 to {EXIT_CHOICE}.")
            continue

        script_name, title = task
        print(f"\nStarting: {title}")
        run_task(script_name)


# Python always sets a special variable called __name__ in every module.
# It starts main_app() when you launch app.py as a program, and skips it if something else imports app.

if __name__ == "__main__":
    main_app()


# How the file is used	What __name__ is	Does main_app() run automatically?
# python app.py           "__main__"          Yes
# import app              "app"               No