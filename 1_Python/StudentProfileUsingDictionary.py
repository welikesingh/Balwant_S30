#Student Profile Using Dictionary
student = {
        "name": "Rahul",
        "age": 22,
        "course": "Python",
        "city": "Bangalore",
        "marks": 88
        }

print("Print the complete dictionary :")
print(student)

print("Print the student's name", student['name'])
print("Print their course", student["course"] )

print(" Print all keys :", student.keys())
print(" Print all values :", student.values())

print("Print all key-value pairs :",student.items())
print("Change marks from 88 to 92 :")
student["marks"] = 92

print("Add \"email\" :")
student["email"]="welikesingh@gmail.com"
print(student)


print("Add phone")
student["phone"]="Android"
print(student)

print("Remove city")
student.pop("city")
print(student)

print("Use get() to retrieve name",student.get("name"))

print("Create a copy of the dictionary:")
student_copy= student
print(student_copy)


print(""" Explain
keys()
values()
items()
get()
update()
pop()
copy() """
)

print(student.keys())
print(student.values())
print(student.items())
print(student.get("name"))
#inserts the specified items to the dictionary
student.update({"college":"University of oklahoma"}) 
print(student)

student.pop("college")
print(student)

#Shallow Copy # Item get copied in another location and no reference maintained
new_student_swallow= student.copy()
print(new_student_swallow)

new_student_swallow["name"] = "Balwant"
print( new_student_swallow)
print(student)



# Deep copy: Copied disctionary hold pointer of original
new_student_deep= student
print(new_student_deep)

new_student_deep["name"] = "Singh"
print(new_student_deep)
print(student)