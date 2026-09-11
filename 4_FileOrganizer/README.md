# File Organizer

Python program that organizes files from a folder into subfolders based on their extensions.

Examples:

- `photo.jpg` → `Images/`
- `notes.txt` → `Text/`
- `report.pdf` → `Documents/`
- `data.csv` → `Data/`

## How to run it

From this project folder:

```text
python main.py
```

That organizes files inside `sample_files`.

To organize a different folder, pass the path as an argument:


After each run, check `organizer.log` for a record of every successful and failed file operation.

To support more file types, add entries to `EXTENSION_MAP` in `file_detector.py` (for example `".svg": "Images"`).

# exact operation that performs the move is: source_file.replace(destination_file)
source_file = the file you want to move
destination_file = where you want the file to go
.replace() moves the file to that destination  


## Project layout

| File | Job |
|------|-----|
| `exceptions.py` | Custom errors, including `UnsupportedFileError` |
| `file_detector.py` | Looks at the extension and picks a folder |
| `file_mover.py` | Creates folders and moves files |
| `app_logger.py` | Writes results to `organizer.log` |
| `main.py` | Ties the modules together |
| `sample_files/` | Example files you can use for a first run |

## What each error case does

- **File does not exist** → raises `SourceFileNotFoundError` and logs a failure
- **Destination folder missing** → creates the folder automatically; if that fails, raises `DestinationFolderError`
- **Duplicate filename** → keeps both files by renaming (`photo.jpg` and `photo_1.jpg`); can also raise `DuplicateFileError` if renaming is turned off
- **Permission error** → caught as `PermissionError` and logged
- **Unsupported type** → raises `UnsupportedFileError` and leaves the file in place
- **No extension** → treated as unsupported and logged as a failure

