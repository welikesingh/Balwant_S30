message = " Welcome To Python Programming Class "
print("Remove extra spaces: ",message.strip())
print("Convert everything to lowercase: ",message.lower())
print("Convert everything to uppercase: ",message.upper())
print("Convert to title case: ",message.lower().title())
print("Replace \"Python\" with \"Advanced Python\"",message.replace("Python","Advanced Python"))
print("Check whether the string starts with \"Welcome\"",message.strip().startswith("Welcome"))
print("Check whether it ends with \"Class\"",message.strip().endswith("Class"))
print("Count occurrences of \"o\"",message.count('o') )
#print("Find the position of \"Programming\"",message.index("Programming"))
print("Find the position of \"Programming\"",message.find("Programming"))
print("Split the sentence into words: ", message.split())

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