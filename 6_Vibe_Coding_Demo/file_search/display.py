"""Console formatting helpers for search results and errors."""

from collections.abc import Iterable
import logging
from pathlib import Path

from file_search.filters import FILE_TYPES
from file_search.logging_config import LOGGER_NAME


logger = logging.getLogger(LOGGER_NAME)


def show_file_type_help() -> None:
    """Display supported file-type names and their extensions."""
    print("\nAvailable file types:")
    for file_type, extensions in FILE_TYPES.items():
        examples = ", ".join(sorted(extensions))
        print(f"  {file_type:<12} {examples}")


def _display_path(path: Path, root: Path) -> str:
    """Return a readable path, relative to the search root when possible."""
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def show_results(results: Iterable[Path], root: Path) -> None:
    """Print matching paths and a short result summary."""
    paths = list(results)

    print("\nResults")
    print("-------")

    if not paths:
        print("No matching files found.")
        logger.info("Search completed with no matching files")
        return

    for path in paths:
        display_path = _display_path(Path(path), root)
        print(display_path)
        logger.debug("Result: %s", display_path)

    label = "result" if len(paths) == 1 else "results"
    logger.info("%d %s found", len(paths), label)


def show_error(message: str) -> None:
    """Print an application error in a consistent format."""
    logger.error("%s", message)
