"""Command-line entry point for the file search tool."""

from collections.abc import Callable
from datetime import date, datetime
import logging
from pathlib import Path

from file_search.display import show_error, show_file_type_help, show_results
from file_search.exceptions import FileSearchError
from file_search.logging_config import LOGGER_NAME, setup_logging
from file_search.scanner import list_all_files
from file_search.search import (
    search_by_creation_date,
    search_by_extension,
    search_by_file_type,
    search_by_folder,
    search_by_name,
)


logger = logging.getLogger(LOGGER_NAME)
SearchAction = Callable[[Path], list[Path]]


def prompt_for_date() -> date:
    """Ask for a date until the user enters it in YYYY-MM-DD format."""
    while True:
        value = input("Creation date (YYYY-MM-DD): ").strip()
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            print("Please enter a valid date in YYYY-MM-DD format.")


def _list_files(root: Path) -> list[Path]:
    logger.info("Listing all files")
    return list_all_files(root)


def _search_name(root: Path) -> list[Path]:
    query = input("File name: ").strip()
    logger.info("Searching by file name: %s", query)
    return search_by_name(root, query)


def _search_extension(root: Path) -> list[Path]:
    extension = input("Extension (for example, pdf or .pdf): ").strip()
    logger.info("Searching by extension: %s", extension)
    return search_by_extension(root, extension)


def _search_type(root: Path) -> list[Path]:
    show_file_type_help()
    file_type = input("Enter a file type from the list above(Example: document): ").strip()
    logger.info("Searching by file type: %s", file_type)
    return search_by_file_type(root, file_type)


def _search_date(root: Path) -> list[Path]:
    creation_date = prompt_for_date()
    logger.info("Searching by creation date: %s", creation_date)
    return search_by_creation_date(root, creation_date)


def _search_folder(root: Path) -> list[Path]:
    folder = input("Folder name or path: ").strip()
    logger.info("Searching by folder: %s", folder)
    return search_by_folder(root, folder)


MENU_ACTIONS: dict[str, tuple[str, SearchAction]] = {
    "1": ("List all files", _list_files),
    "2": ("Search by file name", _search_name),
    "3": ("Search by extension", _search_extension),
    "4": ("Search by file type", _search_type),
    "5": ("Search by date created", _search_date),
    "6": ("Search by folder", _search_folder),
}
EXIT_CHOICE = "7"


def display_menu() -> None:
    """Display menu options generated from the action registry."""
    print("\nFile Search Tool")
    print("----------------")
    for choice, (label, _) in MENU_ACTIONS.items():
        print(f"{choice}. {label}")
    print(f"{EXIT_CHOICE}. Exit")


def handle_choice(choice: str, root: Path) -> bool:
    """Run the selected action. Return False when the program should exit."""
    logger.debug("Menu option selected: %s", choice)
    if choice == EXIT_CHOICE:
        logger.info("Application closed by user")
        print("Goodbye!")
        return False

    menu_item = MENU_ACTIONS.get(choice)
    if menu_item is None:
        print("Invalid choice. Please select a number from 1 to 7.")
        return True

    _, action = menu_item
    results = action(root)
    show_results(results, root)
    return True


def main() -> None:
    """Display the menu and coordinate user actions."""
    root = Path.cwd()
    log_path = setup_logging(root)
    logger.info("File Search Tool started")
    logger.info("Search root: %s", root)
    logger.info("Log file: %s", log_path)
    print(f"Searching in: {root}")

    while True:
        try:
            display_menu()
            choice = input("Choose an option: ").strip()
            if not handle_choice(choice, root):
                break
        except FileSearchError as error:
            show_error(str(error))
        except PermissionError as error:
            show_error(f"Permission denied: {error}")
        except OSError as error:
            show_error(str(error))
        except (KeyboardInterrupt, EOFError):
            logger.info("Search cancelled by user")
            print("\nSearch cancelled. Goodbye!")
            break


if __name__ == "__main__":
    main()
