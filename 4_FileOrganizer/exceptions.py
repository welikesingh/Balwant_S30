"""Custom exceptions used by the file organizer."""


class FileOrganizerError(Exception):
    """Base error for all organizer problems."""


class UnsupportedFileError(FileOrganizerError):
    """Raised when a file extension is not in the supported list."""


class DestinationFolderError(FileOrganizerError):
    """Raised when a destination folder is missing and cannot be created."""


class DuplicateFileError(FileOrganizerError):
    """Raised when a file with the same name already exists in the destination."""


class SourceFileNotFoundError(FileOrganizerError):
    """Raised when the source file path does not exist."""
