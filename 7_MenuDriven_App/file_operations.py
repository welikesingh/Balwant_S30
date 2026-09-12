from exception_handler import handle_error


def read_file(logger):
    """Read and display the contents of a text file."""
    file_name = input("Enter the file name to read: ").strip()
    logger.debug("Trying to read file: %s", file_name)
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            content = file.read()
        if content:
            print("\nFile contents:")
            print(content)
            logger.info("File read successfully")
        else:
            logger.warning("File was empty")
            print("The file is empty.")
    except (OSError, UnicodeError) as error:
        handle_error(logger, error, "The file could not be opened.")


def write_file(logger):
    """Write text entered by the user to a file."""
    file_name = input("Enter the file name to write: ").strip()
    text = input("Enter the text: ")
    logger.debug("Trying to write file: %s", file_name)
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(text)
        logger.info("File written successfully")
        print("File written successfully.")
    except (OSError, UnicodeError) as error:
        handle_error(logger, error, "The file could not be written.")
