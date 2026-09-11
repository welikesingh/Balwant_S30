# Student Result Management System

Menu-driven Python program to store student details, take marks for 5 subjects, and calculate total, percentage, grade, and pass/fail.

## Run

```bash
python main.py
```

## Menu

1. Add new student  
2. Process students  
3. Search student  
4. Delete a student record  
5. Update student record  
6. Exit  

## Modules

- `main.py` — menu and user input  
- `student_ops.py` — add, search, update, delete, save/load  
- `result_calc.py` — total, percentage, grade, pass/fail  
- `exceptions.py` — custom errors (`InvalidMarksError`, etc.)  
- `logger_config.py` — error logging  

## Notes

- Subjects: Maths, Science, English, Social, Computer  
- Marks must be numeric and between 0 and 100  
- Pass mark is 40 in each subject and 40% overall  
- If one student record fails during processing, the error is logged and the rest continue  
- Records are saved in `students.json`  
- Errors are written to `logs/student_system.log`  
