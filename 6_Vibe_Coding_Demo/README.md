# File Search Tool

A small command-line application for finding files in the current directory and
its subfolders.

## Features

- List all files
- Search by file name or extension
- Search by file type, such as document, image, audio, video, or code
- Search by creation date
- Search within a folder
- Display activity in the console
- Save each run to a timestamped file in the `logs/` folder

## Requirements

- Python 3.10 or newer
- No external packages

## Run the application

Open a terminal in the project directory and run:

```powershell
python main.py
```

Select an option from the displayed menu and enter the requested search value.
The directory from which the application is started becomes the search root.

## Project structure

```text
file_search/
├── display.py
├── exceptions.py
├── filters.py
├── logging_config.py
├── metadata.py
├── scanner.py
└── search.py
main.py
```
