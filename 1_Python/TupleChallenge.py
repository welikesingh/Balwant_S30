# Tuple Challenge
technologies = ("Python", "Java", "Python", "C++", "JavaScript", "Python")

print("Print the tuple : ",technologies )
print("Print its type : ",type(technologies))
print("Print the first item :" ,technologies[0])
print("Print the last item: ", technologies[-1])

print("Slice the tuple :", technologies[1:3]) #tuple_name[start:stop:step]

print("Count \"Python\" :",technologies.count("Python") )

print("Find the index of \"C++\" :", technologies.index("C++"))

# print("Find the index of \"C+++++\" :", technologies.index("C+++++")) 
# # index function will throw exception for non existing element 
# We can define own custom function for this
def find_index(tup, item):
    try:
        return tup.index(item)
    except ValueError:
        return None
    
print("Find the index of \"C+++++\" :", find_index( technologies, "C+++++"))

print("Find the tuple length :", len(technologies))

print(" Convert the tuple into a list: ")
list2= list(technologies)
print(list2)
print("Type: ", type(list2))
print(" Convert the tuple into a list: ",list(technologies))


print("Add \"Go\" after converting it into a list")
list2.append('Go')
print(list2)
print("Convert it back into a tuple :", list2)
tup=tuple(list2)
print("Tupe of tup: ", type(tup), " Tuple Elements: ",tup)


print("Explain why tuples are called immutable.:")
tup[0]='Balwant'
# Try to update any element it will throw exception 
# 'tuple' object does not support item assignment
