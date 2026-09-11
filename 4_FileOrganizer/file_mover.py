"""Move a file into the correct destination folder."""

from pathlib import Path

from exceptions import (
    DestinationFolderError,
    DuplicateFileError,
    SourceFileNotFoundError,
)


def ensure_destination(destination_folder: Path) -> None:
    """Create the destination folder if it is missing."""
    try:
        destination_folder.mkdir(parents=True, exist_ok=True)
    except PermissionError as error:
        raise DestinationFolderError(
            f"Cannot create folder '{destination_folder}': permission denied."
        ) from error
    except OSError as error:
        raise DestinationFolderError(
            f"Cannot create folder '{destination_folder}': {error}"
        ) from error


def unique_destination(destination_file: Path) -> Path:
    """
    If photo.jpg already exists, use photo_1.jpg, photo_2.jpg, and so on.

    This avoids overwriting a file that is already in the destination folder.
    """
    if not destination_file.exists():
        return destination_file

    stem = destination_file.stem
    suffix = destination_file.suffix
    parent = destination_file.parent
    counter = 1

    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def move_file(
    source_file: Path,
    destination_folder: Path,
    *,
    overwrite: bool = False,
    rename_duplicates: bool = True,
) -> Path:
    """
    Move source_file into destination_folder.

    Returns the final path of the moved file.

    Raises:
        SourceFileNotFoundError: source path is missing
        DestinationFolderError: destination cannot be created
        DuplicateFileError: same name already exists and renaming is disabled
        PermissionError: the operating system blocks the move
    """
    if not source_file.exists():
        raise SourceFileNotFoundError(f"File not found: '{source_file}'")

    if not source_file.is_file():
        raise SourceFileNotFoundError(
            f"'{source_file}' exists but is not a regular file."
        )

    ensure_destination(destination_folder)

    destination_file = destination_folder / source_file.name

    if destination_file.exists() and not overwrite:
        if rename_duplicates:
            # Keep both files: photo.jpg stays, new one becomes photo_1.jpg
            destination_file = unique_destination(destination_file)
        else:
            raise DuplicateFileError(
                f"A file named '{source_file.name}' already exists in "
                f"'{destination_folder}'."
            )

    try:
        source_file.replace(destination_file)
    except PermissionError:
        raise
    except OSError as error:
        raise PermissionError(
            f"Could not move '{source_file.name}': {error}"
        ) from error

    return destination_file
