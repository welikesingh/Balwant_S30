#Remove Duplicate Data Using Sets

numbers = [10, 20, 30, 20, 40, 10, 50, 30, 60]

print("Print the original list: ",numbers)
print("Convert the list into a set")
set1=set(numbers)
print(set1)
print("Observe which duplicates disappear: 10, 20, 30 ")

print("Convert the set back into a list: ",list(set1) )

print("Print the number of original elements: ", len(numbers))

print("Print the number of unique elements: ", len(list(set1)))

print("Create another example using duplicate student names.")
student=["Student1", "Student2", "Student1", "Student2", "Student3"]
print(student)

print("Explain why sets are useful when working with duplicate data.")
print("Set keep only unique element")
set2={1,1,1,1,2,3,4,5}
print(set2)

