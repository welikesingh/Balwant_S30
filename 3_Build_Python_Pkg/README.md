# calculator_tools

A small reusable Python **package** for arithmetic, percentage, average, temperature conversion, and simple length conversion.

This project uses **functions**, **loops**, **modules**, **packages**, and **imports**. 

## How to run

From this project folder:

```bash
python main.py
```

`main.py` imports the `calculator_tools` package and shows working examples plus error cases.

---

## Function vs module vs package vs import

### Function

A **function** is a named block of code that does one job. You call it and it can return a value.

Examples in this project: `add(10, 5)`, `average([10, 20, 30])`, `convert_length(1, "km", "m")`.

A function lives inside a file.

### Module

A **module** is one `.py` file. That file can contain several functions.

| File | What is inside |
|------|----------------|
| `calculator_tools/arithmetic.py` | `add`, `subtract`, `multiply`, `divide` |
| `calculator_tools/statistics.py` | `percentage`, `average` |
| `calculator_tools/converter.py` | temperature and length conversion |
| `calculator_tools/exceptions.py` | custom error name `InvalidOperationError` |
| `main.py` | demo script (this is also a module) |

### Package

A **package** is a folder of related modules. The folder must contain `__init__.py`.

```
calculator_tools/          ← package (folder)
    __init__.py            ← tells Python this folder is a package
    arithmetic.py          ← module
    statistics.py          ← module
    converter.py           ← module
    exceptions.py          ← module
```

`__init__.py` can stay empty. It only marks the folder as a package. Import functions from the modules:

```python
from calculator_tools.arithmetic import add
from calculator_tools.statistics import average
```

A package is for reuse. `main.py` imports those modules instead of putting every function in one file.

### Import

**Import** is how one file uses code from another module or package.

```python
# Import selected functions from a module (used in main.py)
from calculator_tools.arithmetic import add, divide
from calculator_tools.exceptions import InvalidOperationError

# Import one module from the package
from calculator_tools import arithmetic
print(arithmetic.multiply(4, 5))

# Import one function from one module
from calculator_tools.converter import convert_temperature
```

`main.py` is not the library. It **imports** `calculator_tools` and calls the functions.

---

## Quick comparison: function vs module vs package

| | Function | Module | Package |
|--|----------|--------|---------|
| **What it is** | A named block of code that does one job | One `.py` file | A folder of related modules |
| **Contains** | Steps that run when you call it | One or more functions (and other names) | Several modules plus `__init__.py` |
| **You use it by** | Calling it, e.g. `add(10, 5)` | Importing the file | Importing a module inside the folder |
| **Example here** | `add`, `average`, `convert_length` | `arithmetic.py`, `statistics.py` | `calculator_tools/` |
| **Size / scope** | Smallest piece | One file | Whole library |

**How they nest:** a **function** lives in a **module**; modules live in a **package**.

```
package:  calculator_tools/
module:       arithmetic.py
function:         def add(a, b): ...
```

**Difference in one line each**

- A **function** is code you *call* (`divide(10, 5)`).
- A **module** is a *file* that holds functions (`arithmetic.py`).
- A **package** is a *folder* that groups modules (`calculator_tools/`).

Import is how another file reaches them: `from calculator_tools.arithmetic import add`.

---

## What the functions do

| Function | Module | Purpose |
|----------|--------|---------|
| `add`, `subtract`, `multiply`, `divide` | `arithmetic` | Basic arithmetic |
| `percentage`, `average` | `statistics` | Percent and mean (average uses a `for` loop) |
| `convert_temperature` | `converter` | Convert between C, F, and K |
| `convert_length` | `converter` | Convert between cm, m, and km |

## Errors

Bad input raises **`InvalidOperationError`** (see `exceptions.py`), for example:

- division by zero
- a string where a number is needed
- an empty list for average
- an unsupported unit like `"mile"`
