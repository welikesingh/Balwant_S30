
# Set Operations Challenge

python_students = {"Rahul", "Aman", "Priya", "Karan", "Neha"}
java_students = {"Priya", "Karan", "Rohit", "Simran"}

print( f"Print both sets: {python_students} , {java_students}")

# set_b = {3, 4, 5, 6}
# print(" union for 3 sets :", python_students.union(java_students,set_b))
print(" Find students learning either Python or Java ", python_students.union(java_students))

print(" Find students learning both : ", python_students.intersection(java_students))

print(" Find students learning only Python ", python_students)

print(" Find students learning only Java : ", java_students)

print(" Find students belonging to exactly one group : ", python_students.symmetric_difference(java_students) )

print(" Add a new student:  ")
python_students.add("Balwant")
print(python_students)

print(" Remove a student : " )
python_students.remove("Balwant") # if element is not in set then it raise error
print(python_students)

print("Demonstrate discard()") # it donot raise on removing element when element isnot preset in set
python_students.discard('Priya')
print(python_students)
python_students.discard('Priya')

print(python_students)
