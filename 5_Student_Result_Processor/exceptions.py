class InvalidMarksError(Exception):
    """Raised when marks are not in the 0-100 range or look incorrect."""
    pass


class MissingStudentInfoError(Exception):
    """Raised when name, roll number, or subject marks are missing."""
    pass


class StudentNotFoundError(Exception):
    """Raised when a student roll number is not in the records."""
    pass
