"""
File Organizer
--------------
Moves files from a folder into subfolders based on their extensions.

Example:
    photo.jpg  -> Images/
    notes.txt  -> Text/
    report.pdf -> Documents/
    data.csv   -> Data/

Usage:
    python main.py
"""

from pathlib import Path
import sys

from app_logger import log_failure, log_success, setup_logger
from exceptions import (
    DestinationFolderError,
    DuplicateFileError,
    SourceFileNotFoundError,
    UnsupportedFileError,
)
from file_detector import get_category
from file_mover import move_file

# # Skip these names so the program does not move its own code or log file.
# SKIP_NAMES = {
#     "main.py",
#     "file_detector.py",
#     "file_mover.py",
#     "app_logger.py",
#     "exceptions.py",
#     "organizer.log",
#     "README.md"
# }


def organize_folder(source_folder: Path) -> None:
    logger = setup_logger()

    if not source_folder.exists():
        log_failure(logger, f"Source folder does not exist: {source_folder}")
        print(f"Folder not found: {source_folder}")
        return

    if not source_folder.is_dir():
        log_failure(logger, f"Path is not a folder: {source_folder}")
        print(f"Not a folder: {source_folder}")
        return

    files = [item for item in source_folder.iterdir() if item.is_file()]
    if not files:
        print(f"No files to organize in: {source_folder}")
        return

    print(f"Organizing files in: {source_folder}\n")

    for source_file in files:
        # if source_file.name in SKIP_NAMES:
        #     continue
        #print('File: ',source_file)
        try:
            category = get_category(source_file)
            destination_folder = source_folder / category
            final_path = move_file(source_file, destination_folder)
            log_success(
                logger,
                f"Moved '{source_file.name}' -> '{final_path.relative_to(source_folder)}'",
            )
        except UnsupportedFileError as error:
            log_failure(logger, str(error))
        except SourceFileNotFoundError as error:
            log_failure(logger, str(error))
        except DestinationFolderError as error:
            log_failure(logger, str(error))
        except DuplicateFileError as error:
            log_failure(logger, str(error))
        except PermissionError as error:
            log_failure(
                logger,
                f"Permission error while moving '{source_file.name}': {error}",
            )
        except Exception as error:
            log_failure(
                logger,
                f"Unexpected error for '{source_file.name}': {error}",
            )


def main() -> None:
    source_folder = Path(__file__).parent / "sample_files"
    #print("---------",source_folder,"---------",__file__,"---",Path.cwd(),'---',Path(__file__).parent)
    organize_folder(source_folder)
    print("\nDone. Check organizer.log for a full record of successes and failures.")


if __name__ == "__main__":
    main()
