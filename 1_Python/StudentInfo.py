#Student Information String Challenge
student = "python programming for data science"
print("Print the complete string:",student)
print("Print the first character: ",student[0])
print("Print the last character:",student[-1])
print("Print the first 6 characters:",student[0:6]) # Start is included, End is excluded
print("Print the last 7 characters:",student[-7:])
print("Reverse the string using slicing:",student[::-1],"".join((reversed(student)) ))
print("Convert it to uppercase: ",student.upper())
print("Convert it to lowercase: ",student.lower())
print("Convert it to title case: ", student.title())
print("Count how many times \"a\" appears: ",student.count('a'))
print("Find the position of \"programming\"", student.find('programming'))
print("Replace \"data science\" with \"artificial intelligence\"",student.replace('data science','artificial intelligence'))
print("Split the string into individual words:", student.split())


print("---------------Function Explanation-----------")
print("""
strip() → Removes leading and trailing whitespace from a string")
lower() → Converts all characters in a string to lowercase
upper() → Converts all characters in a string to uppercase
title() → Converts the first letter of each word to uppercase (title case)
replace() → Replaces all occurrences of a specified substring with another string
find() → Returns the index of the first occurrence of a substring; returns -1 if not found
count() → Returns the number of occurrences of a substring in a string
""")
