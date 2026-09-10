# Combine Loops and Functions

A collection of small Python programs that practice **functions**, **`for` / `while` loops**, and **menu-driven input**. A main launcher (`app.py`) lets you pick any program without editing the individual task files.

## Project objective

Apply loops and functions together in practical mini-applications instead of isolated examples.

Each program should:

- Break work into named functions (calculate, display, validate, search, and so on)
- Use loops for repeated input, menus, lists, and ranges
- Accept user input and show clear results
- Stay runnable on its own (`python task_01.py`) **and** from the combined menu (`python app.py`)

The final utility app (`task_12_utility_app.py`) puts several tools behind one inner menu to show how a larger program is built from smaller functions.

## Programs completed

| File | Program | What it does |
|------|---------|----------------|
| `task_01.py` | Student Result Management | Accepts marks, total, percentage, grade, pass/fail, and prints a result sheet |
| `task_02.py` | Banking Application | Check balance, deposit, withdraw (menu + `while` loop) |
| `task_03.py` | Inventory Management | Add, display, search, and update product quantity |
| `task_04.py` | Quiz Application | Five Python questions, scoring, and final percentage |
| `task_05.py` | Number Analysis Tool | Largest, smallest, total, average, even/odd, positive/negative (without `min`/`max`/`sum`) |
| `task_06.py` | Employee Salary Analyzer | Payroll total, average, highest/lowest, employees above average |
| `task_07.py` | Shopping Cart | Add/remove items, view cart, calculate bill until Exit |
| `task_08.py` | Password Strength Checker | Checks length, upper, lower, digit, and special character |
| `task_09.py` | Prime Number Analyzer | Primes in a range: list, count, sum, largest prime |
| `task_10.py` | Expense Tracker | Add, view, total, and highest expense |
| `task_11.py` | Mini Authentication System | Login with limited attempts, session menu, logout |
| `task_12_utility_app.py` | Python Utility Application | Combined menu: calculator, palindrome, prime, factorial, multiplication table, number analyzer, password checker |
| `app.py` | Main launcher | Numbered menu that runs each task file, then returns to the main menu |

## How to execute the programs

**Requirement:** Python 3 installed. Open a terminal in this folder:

`Combine_Loops_Functions`

### Option 1 — Main menu (recommended)

```text
python app.py
```

Then enter a number:

- `1`–`12` — run the matching task
- `13` — exit the launcher

When a task finishes (or you exit its inner menu), control returns to the main menu so you can pick another program.

### Option 2 — Run one file directly

```text
python task_01.py
python task_02.py
python task_12_utility_app.py
```

Replace the filename with any `task_XX.py` you want to test.

### Notes

- Programs are interactive: they wait for keyboard input.
- `app.py` starts each task as a separate process (same as running that file yourself), so task files do not need to be changed for the launcher to work.
- See the next section for why `if __name__ == "__main__":` is used in some files.

## Why `if __name__ == "__main__":` is used

Python gives every file a built-in variable named `__name__`. Its value depends on **how** the file is started, not on what is written inside the functions.

| How you start the file | What `__name__` contains | Typical result |
|------------------------|--------------------------|----------------|
| `python app.py` | `"__main__"` | The file is the program being run |
| `import app` | `"app"` | The file is loaded as a module (name comes from `app.py`) |
| `python task_12_utility_app.py` | `"__main__"` | The utility menu is the program being run |
| `import task_12_utility_app` | `"task_12_utility_app"` | Functions load; the menu does not start by itself |

The `if` check means: **run the starter function only when this file is the main program.**

Without the guard, any `import` of that file would immediately enter a `while True` menu and wait for input. That makes the file hard to reuse. With the guard, you can still run `python app.py` as usual, and you can also import functions later without launching the menu.

### Files in this project that use it

**`app.py`**

```python
if __name__ == "__main__":
    main_app()
```

- Running `python app.py` sets `__name__` to `"__main__"`, so `main_app()` starts the numbered launcher.
- If another script did `import app`, `__name__` would be `"app"`, so the launcher would not start automatically. Functions such as `main_app()` and `run_task()` would still be available to call on purpose.

**`task_12_utility_app.py`**

```python
if __name__ == "__main__":
    utility_app()
```

- Running `python task_12_utility_app.py` sets `__name__` to `"__main__"`, so `utility_app()` starts the inner utility menu.
- Importing the file would set `__name__` to `"task_12_utility_app"`, so only the helper functions (calculator, palindrome checker, and so on) would load.

When you pick option **12** from `app.py`, the launcher runs `python task_12_utility_app.py` in a new process. In that process the task file is the main program, so `__name__` is still `"__main__"` and the utility menu starts.

### Files that do not use it

`task_01.py` through `task_11.py` run their menus and demos at **top level** (code outside any function). That is why they work when you run them directly, and why `app.py` starts them as separate programs instead of importing them.

If those files were imported with `import task_01`, Python would still execute that top-level `while` loop immediately. They were left unchanged so each assignment file stays independently runnable. The `__name__` pattern was added on the combined launcher (`app.py`) and the combined utility app (`task_12_utility_app.py`), where a clear “start the menu only when executed” entry point is useful.

## Concepts used

- **Functions** — reusable steps (accept input, calculate, check, display)
- **`while` loops** — menus that keep running until Exit
- **`for` loops** — lists of marks, quiz questions, ranges of primes, character checks
- **Conditional logic** — `if` / `elif` / `else` for menus, grades, pass/fail, prime tests
- **User input and validation** — `input()`, `int()` / `float()`, `try` / `except` where invalid numbers must be rejected
- **Data structures** — lists (marks, expenses, products), dictionaries (cart, employee salaries, quiz items)
- **`global` state** — shared balance in the banking demo
- **String processing** — palindrome cleanup, password character classes
- **Program structure** — `if __name__ == "__main__":` as the entry point
- **Process launcher** — `subprocess` in `app.py` to run each task independently

## Your learning / outcomes

After this project you should be able to:

1. Split a problem into functions instead of one long script.
2. Build a menu with a `while True` loop and `if`/`elif` choices.
3. Combine loops and functions (a function that loops, a loop that calls functions).
4. Store related data in lists and dictionaries and walk through them with a loop.
5. Validate input and handle simple errors without crashing.
6. Keep each task as its own file and still offer one entry point (`app.py`).
7. Understand `__name__`: it is `"__main__"` when a file is executed, and the module name (for example `"app"`) when it is imported.

The utility application in `task_12_utility_app.py` is the capstone: several independent tools behind one menu, each implemented as its own function.
