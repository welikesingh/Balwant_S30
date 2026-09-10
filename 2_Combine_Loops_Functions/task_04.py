print("4.---Quiz Application---")
print("""
Create at least 5 Python questions.
The application should display one question at a time
accept answers
check answers
maintain score
show final percentage
""")

# List of dictionaries containing questions, options, and the correct answer
quiz = [
    {
        "question": "What is the correct file extension for Python files?",
        "options": ["A) .pt", "B) .py", "C) .pyt", "D) .python"],
        "answer": "B",
    },
    {
        "question": "Which keyword is used to define a function in Python?",
        "options": ["A) func", "B) define", "C) def", "D) function"],
        "answer": "C",
    },
    {
        "question": "Which symbol is used for single-line comments in Python?",
        "options": ["A) //", "B) #", "C) /*", "D) <!--"],
        "answer": "B",
    },
    {
        "question": "What is the output of `2 ** 3` in Python?",
        "options": ["A) 6", "B) 8", "C) 9", "D) 16"],
        "answer": "B",
    },
    {
        "question": "Which built-in function is used to get the length of a list?",
        "options": ["A) size()", "B) length()", "C) len()", "D) count()"],
        "answer": "C",
    },
]


score = 0
total_questions = len(quiz)

# Loop each question one at a time
for index, q in enumerate(quiz, start=1):
  print(f"\nQuestion {index}: {q['question']}")
  for option in q["options"]:
    print(option)

  # Accept user answer
  user_ans = input("Your answer (A, B, C, or D): ").strip().upper()

  # Check answer
  if user_ans == q["answer"]:
    print("Correct!")
    score += 1
  else:
    print(f"Wrong. The correct answer was {q['answer']}.")

# Calculate final percentage
percentage = (score / total_questions) * 100

# Show final results
print("\n--- Quiz Finished ---")
print(f"Your score: {score} out of {total_questions}")
print(f"Final percentage: {percentage:.2f}%")
