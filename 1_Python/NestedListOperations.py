#Nested List Challenge
#Indexing a nested list in Python works by using multiple sets of square brackets [] in sequence. 
# Each set of brackets moves you one layer deeper into the list.
students = [
["Rahul", 21, "Python"],
["Priya", 22, "Data Science"],
["Aman", 20, "Machine Learning"]
]

print("Print the complete list: ",students)

print("Print Rahul's name: ",students[0][0])

print("Print Priya's age: ",students[1][1])

print("Print Aman's course: ",students[2][2])

print("Print the complete record of Priya: ",students[1])

print("Change Rahul's course to \"AI\"")
students[0][2]="AI"
print(students)


print("Add another student record manually")
students.append(["Balwant",44,"MLOps"])
print(students)
