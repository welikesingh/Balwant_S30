# Create a Student Marks List

marks = [78, 85, 90, 67, 88, 92, 76]

print("Print the complete list :",marks)
print("Print the first element :",marks[0])
print("Print the last  :", marks[-1])
print("Print elements from index 2 to 5 :", marks[2:6])
print("Find the number of elements :", len(marks))


print("Find maximum marks :",  max(marks))
print("Find minimum marks :", min(marks))
print("Find total marks :", sum(marks))

print(" Sort marks in ascending order :")
marks.sort()
print(marks)

print("Sort marks in descending order :")
marks.sort(reverse=True)
print(marks)

print(" Add 95 :")
marks.append(95)
print(marks)

print("Add [81, 84] :")
marks.append([81, 84])
print(marks)

print("Remove 67:")
marks.remove(67)
print(marks)

print("Count how many times 90 occurs :",marks.count(90))
print("Find the index of 88 :", marks.index(88))