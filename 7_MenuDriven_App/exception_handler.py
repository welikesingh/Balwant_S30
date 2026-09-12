"""Reusable exception handlers for the application."""


def handle_error(logger, error, message):
    """Handle an expected error without closing the application."""
    logger.error("%s Details: %s", message, error)
    print(message)


def handle_critical_error(logger):
    """Handle an unexpected error without closing the application."""
    logger.critical("Unexpected application failure", exc_info=True)
    print("An unexpected error occurred. You may continue using the application.")
