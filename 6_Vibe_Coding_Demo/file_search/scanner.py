"""File-system scanning utilities."""

from pathlib import Path

from file_search.exceptions import InvalidRootError, ScanError


def _validate_root(root: Path) -> Path:
    """Return a normalized directory path or raise a helpful error."""
    root = Path(root).expanduser()
    try:
        if not root.exists():
            raise InvalidRootError(f"Search folder does not exist: {root}")
        if not root.is_dir():
            raise InvalidRootError(f"Search location is not a folder: {root}")
    except OSError as error:
        raise ScanError(f"Could not access search folder {root}: {error}") from error

    return root


def scan_files(root: Path, recursive: bool = True) -> list[Path]:
    """Return files found under *root* in a predictable order."""
    root = _validate_root(root)
    try:
        entries = root.rglob("*") if recursive else root.iterdir()
        files = [entry for entry in entries if entry.is_file()]
    except (PermissionError, OSError) as error:
        raise ScanError(f"Could not scan folder {root}: {error}") from error

    return sorted(files, key=lambda path: str(path).casefold())


def list_all_files(root: Path) -> list[Path]:
    """Return every file contained in *root* and its subfolders."""
    return scan_files(root, recursive=True)
