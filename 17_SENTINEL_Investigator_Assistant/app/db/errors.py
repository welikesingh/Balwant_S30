class DatabaseUnavailable(Exception):
    """A database could not be reached or a query failed.

    The message is safe to show to API clients: it never contains credentials.
    """
