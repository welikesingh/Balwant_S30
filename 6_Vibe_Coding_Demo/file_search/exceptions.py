"""Exceptions raised by the file search package."""


class FileSearchError(Exception):
    """Base exception for file-search failures."""


class InvalidSearchError(FileSearchError, ValueError):
    """Raised when a search value is empty or unsupported."""


class MetadataError(FileSearchError, OSError):
    """Raised when file metadata cannot be read."""


class InvalidRootError(FileSearchError, ValueError):
    """Raised when the selected search root is not a valid folder."""


class ScanError(FileSearchError, OSError):
    """Raised when a folder cannot be scanned."""
