"""Helpers for reading file metadata."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from file_search.exceptions import MetadataError


@dataclass(frozen=True)
class FileMetadata:
    """Useful metadata collected for one file."""

    path: Path
    size: int
    created_at: datetime
    modified_at: datetime


def get_metadata(path: Path) -> FileMetadata:
    """Read size and timestamp information for *path*."""
    path = Path(path)
    try:
        statistics = path.stat()
    except OSError as error:
        raise MetadataError(f"Could not read metadata for {path}: {error}") from error

    # Windows exposes creation time as st_ctime. 
    # On systems that provide a 
    # birth time explicitly, prefer that value.
    created_timestamp = getattr(statistics, "st_birthtime", statistics.st_ctime)
    return FileMetadata(
        path=path,
        size=statistics.st_size,
        created_at=datetime.fromtimestamp(created_timestamp),
        modified_at=datetime.fromtimestamp(statistics.st_mtime),
    )


def get_creation_date(path: Path) -> datetime:
    """Return the creation timestamp for *path*."""
    return get_metadata(path).created_at

