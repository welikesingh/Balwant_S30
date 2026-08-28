#Shopping Cart Using a Python List
cart = ["Laptop", "Mouse", "Keyboard", "Monitor", "Headphones"]

print("Display all products: ",cart)

print("Access first and last products: ", cart[0]," ", cart[-1])

print("Add \"Webcam\" in list")
cart.append("Webcam") # Adds at last
print(cart)

print("Insert \"USB Hub\" at index 2")
cart.insert(2,"USB Hub")
print(cart)

print("Remove \"Mouse\"")
cart.remove("Mouse")
print(cart)

print("Remove the last item using pop()")
cart.pop()
print(cart)


print("Find the index of \"Monitor\" :")
def find(var1_search: str, cart: list):
  var1_search="Monitor"
  if var1_search in cart:
      idx=cart.index(var1_search)
      return idx
  else:
     return null

print(find("Monitor",cart))



print("Count occurrences of \"Laptop\": ", cart.count("Laptop"))

print("Create a copy of the cart: ")
cart_shallow_copy= cart.copy() # if we change item in the copy, it changes in the original list too
cart_deep_copy=cart 

print("Verify swallow copy change effect")
print( cart_shallow_copy,cart )
cart_shallow_copy[1]="1111"
print( cart_shallow_copy,cart )

print("Verify swallow copy change effect")
print( cart_deep_copy,cart )
cart_deep_copy[2]="2222"
print( cart_deep_copy,cart )


print("Reverse the cart: ",cart[::-1])

print("Sort the products alphabetically: ")
cart.sort()
print(cart)



print(""" 
#Explain the difference between
append() # Adds an element at end
extend() # adds multiple elements at end 
insert() # insert at specific position
remove() # first matching element will be removed
pop()    # remove last element
clear() # make list empty
copy()  # to create copy of all the elements
sort()  # perfomr sorting
reverse() # reverse list
""")

print("Removing")
mylist=[1,2,1,3,4,5,"BAlwant"]
mylist.remove(1)
print(mylist)


print("clearing")
mylist.clear()
print(mylist)

mylist2=[1,2,3,4]

print("Original list: ",mylist2, " Reversed list: ", mylist2.reverse())
