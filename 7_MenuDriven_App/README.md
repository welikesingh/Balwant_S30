# Menu Login Application

A modular, menu-driven Python application demonstrating all standard logging levels and exception handling.

Run it with:

```powershell
              python main.py
```

Demo credentials: `admin` / `password`

Logs are created automatically in `logs/application.log` and `logs/error.log`.

The application log receives DEBUG and higher messages. The error log receives ERROR and CRITICAL messages. 

Messages from INFO through CRITICAL are also shown on the console. 

Shared exception handling is located in `exception_handler.py`.
