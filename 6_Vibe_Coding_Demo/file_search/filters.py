"""Predicates and definitions used to filter scanned files."""

from datetime import date
from pathlib import Path

from file_search.metadata import get_creation_date


FILE_TYPES: dict[str, frozenset[str]] = {
    "document": frozenset({".doc", ".docx", ".odt", ".pdf", ".rtf", ".txt"}),
    "spreadsheet": frozenset({".csv", ".ods", ".xls", ".xlsx"}),
    "presentation": frozenset({".odp", ".ppt", ".pptx"}),
    "image": frozenset(
        {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp"}
    ),
    "audio": frozenset({".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".wma"}),
    "video": frozenset({".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm", ".wmv"}),
    "archive": frozenset({".7z", ".bz2", ".gz", ".rar", ".tar", ".zip"}),
    "code": frozenset(
        {".c", ".cpp", ".css", ".go", ".html", ".java", ".js", ".json", ".py", ".rs", ".ts"}
    ),
}


def normalize_extension(extension: str) -> str:
    """Normalize an extension to lowercase with a leading dot."""
    extension = extension.strip().casefold()
    if extension and not extension.startswith("."):
        extension = f".{extension}"
    return extension


def name_matches(path: Path, query: str) -> bool:
    """Return whether *query* occurs in the file name."""
    return query.casefold() in path.name.casefold()


def extension_matches(path: Path, extension: str) -> bool:
    """Return whether the file has the requested extension."""
    return path.suffix.casefold() == normalize_extension(extension)


def type_matches(path: Path, file_type: str) -> bool:
    """Return whether the file extension belongs to *file_type*."""
    return path.suffix.casefold() in FILE_TYPES[file_type.casefold()]


def creation_date_matches(path: Path, creation_date: date) -> bool:
    """Return whether the file was created on the requested calendar date."""
    return get_creation_date(path).date() == creation_date
