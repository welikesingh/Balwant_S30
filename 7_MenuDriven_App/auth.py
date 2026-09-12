from getpass import getpass

USERNAME = "admin"
PASSWORD = "password"

def login(logger):
    """Ask for credentials and return True when they are correct."""
    username = input("Username: ").strip()
    password = getpass("Password: ")
    logger.debug("Login attempt for username: %s", username)
    if username == USERNAME and password == PASSWORD:
        logger.info("User logged in successfully")
        print("Login successful.")
        return True
    logger.warning("Invalid login attempt")
    print("Invalid username or password.")
    return False

def logout(logger):
    """Log out the current user."""
    logger.info("User logged out")
    print("Logout successful.")
    