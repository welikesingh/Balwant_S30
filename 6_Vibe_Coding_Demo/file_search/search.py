"""High-level file search operations."""

from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from file_search.exceptions import InvalidSearchError
from file_search.filters import (
    FILE_TYPES,
    creation_date_matches,
    extension_matches,
    name_matches,
    normalize_extension,
    type_matches,
)
from file_search.scanner import scan_files


def _required(value: str, label: str) -> str:
    """Return a stripped search value or raise a helpful error."""
    value = value.strip()
    if not value:
        raise InvalidSearchError(f"{label} cannot be empty.")
    return value


def _matching_files(root: Path, predicate: Callable[[Path], bool]) -> list[Path]:
    """Scan once and return files accepted by *predicate*."""
    return [path for path in scan_files(root) if predicate(path)]


def search_by_name(root: Path, query: str) -> list[Path]:
    """Find files whose names contain *query*, ignoring case."""
    query = _required(query, "File name")
    return _matching_files(root, lambda path: name_matches(path, query))


def search_by_extension(root: Path, extension: str) -> list[Path]:
    """Find files with *extension*, with or without its leading dot."""
    extension = normalize_extension(_required(extension, "Extension"))
    return _matching_files(root, lambda path: extension_matches(path, extension))


def search_by_file_type(root: Path, file_type: str) -> list[Path]:
    """Find files belonging to a supported file-type category."""
    file_type = _required(file_type, "File type").casefold()
    if file_type not in FILE_TYPES:
        choices = ", ".join(sorted(FILE_TYPES))
        raise InvalidSearchError(
            f"Unknown file type '{file_type}'. Choose from: {choices}."
        )
    return _matching_files(root, lambda path: type_matches(path, file_type))


def search_by_creation_date(root: Path, creation_date: date | datetime) -> list[Path]:
    """Find files created on *creation_date*."""
    target_date = (
        creation_date.date() if isinstance(creation_date, datetime) else creation_date
    )
    if not isinstance(target_date, date):
        raise InvalidSearchError("Creation date must be a date or datetime value.")
    return _matching_files(
        root, lambda path: creation_date_matches(path, target_date)
    )


def search_by_folder(root: Path, folder: str) -> list[Path]:
    """Find files inside folders whose name or relative path matches *folder*."""
    folder = _required(folder, "Folder")
    root = Path(root)
    requested = Path(folder).expanduser()
    direct_path = requested if requested.is_absolute() else root / requested

    if direct_path.exists():
        if not direct_path.is_dir():
            raise InvalidSearchError(f"Search location is not a folder: {direct_path}")
        return scan_files(direct_path)

    query = folder.replace("\\", "/").strip("/").casefold()

    def folder_matches(path: Path) -> bool:
        relative_parent = path.parent.relative_to(root)
        parent_path = relative_parent.as_posix().casefold()
        parent_names = {part.casefold() for part in relative_parent.parts}
        return query in parent_path or query in parent_names

    return _matching_files(root, folder_matches)
