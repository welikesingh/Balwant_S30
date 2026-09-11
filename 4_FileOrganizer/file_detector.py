"""Decide which folder a file belongs in, based on its extension."""

from pathlib import Path

from exceptions import UnsupportedFileError

# Map lowercase extensions to destination folder names.
EXTENSION_MAP = {
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".webp": "Images",
    ".txt": "Text",
    ".md": "Text",
    ".log": "Text",
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".ppt": "Documents",
    ".pptx": "Documents",
    ".xls": "Documents",
    ".xlsx": "Documents",
    ".csv": "Data",
    ".json": "Data",
    ".xml": "Data",
    ".sql": "Data",
    ".mp3": "Audio",
    ".wav": "Audio",
    ".mp4": "Videos",
    ".mkv": "Videos",
    ".avi": "Videos",
    ".zip": "Archives",
    ".rar": "Archives",
    ".py": "Code",
}


def get_extension(source_file) -> str:
    """Return the file extension in lowercase, for example '.jpg'."""
    return source_file.suffix.lower()


def get_category(source_file) -> str:
    """
    Return the destination folder name for this file.

    Raises:
        UnsupportedFileError: if the extension is not in EXTENSION_MAP.
    """
    extension = get_extension(source_file)

    if not extension:
        raise UnsupportedFileError(
            f"'{source_file.name}' has no extension, so it cannot be organized."
        )

    category = EXTENSION_MAP.get(extension)
    if category is None:
        raise UnsupportedFileError(
            f"'{source_file.name}' has unsupported type '{extension}'."
        )

    return category
