# Build deeper understanding of functions through *args, **kwargs, recursion, lambda functions, scope, 
# and functions working together.
# *args stands for arguments --List
# **kwargs stands for keyword arguments --dictionary

print("------------------------------------------------------------")
print("Create a function using *args that accepts any number of values and returns their total.")
def func_Args(*args):
    tot=0
    for i in args:
      tot=tot + i
    return tot

print("Total: ",func_Args(1,2,3,45))

print("------------------------------------------------------------")

print("Create a function using *args that returns the largest supplied number.")
def func_Largest(*args):
    largest=float('-inf')
    for i in args:
        if i > largest:
          largest=i
    return largest

print("Total: ",func_Largest(1,2,3,45))

print("------------------------------------------------------------")

print("""def create_profile(**kwargs) 
that accepts dynamic user information and prints all provided attributes.""")
def create_profile(**kwargs):
    print(kwargs)

print("All arguments: ")
create_profile(a=1,b=2,c=3,d=45)

print("------------------------------------------------------------")

print("""Create a function that accepts another function as an argument.""")

# 1. Define the higher-order function
def f1_main(*args):
  for func in args:
    func()
    
# 2. Define a simple function to be used as an argument
def d1():
  print(" calling d1 function")

def d2():
  print(" calling d2 function")

print("Printing Function call")
f1_main(d1,d2)
print("------------------------------------------------------------")

#Example
# 1. Define the higher-order function
def calculate(fun,*args):
    return fun(*args)
    
# 2. Define a add/mutiply function to be used as an argument
def add(*args):
  sum=0
  for i in args:
    print(i)
    sum=sum+i
  return sum

def multiply(*args):
  product=1
  for i in args:
    product=product*i
  return product  

print("Calculating Add: ",calculate(add,10,20))
print("Calculating Multiply: ",calculate(multiply,10,20))
print("------------------------------------------------------------")
# map() /filter() function in Python applies a specified function to every item of an
#  iterable (like a list, tuple, or dictionary)

print("""Create a lambda function for calculating the square of a number.""")
input_number = int(input("Enter a number to calculate its square: "))
square = lambda x: x ** 2
print("Square of", input_number, ":", square(input_number))


print("Use lambda with map() to square")
numbers = [1, 2, 3, 4, 5, 6]
squared_numbers = list(map(lambda x: x ** 2, numbers))
print("Squared numbers:", squared_numbers)
print("------------------------------------------------------------")


print("""Use lambda with filter() to extract even numbers.""")
my_list= [1, 2, 3, 4, 5, 6]
even_numbers = list(filter(lambda x: x % 2 == 0, my_list))
print("Even numbers:", even_numbers)


print("------------------------------------------------------------")

print("recursive function to calculate factorial.")
def fact(n: int):
  if n==0 |n == 1:
    return 1
  else:    
    return n*fact(n-1)
print(fact(4))

print("------------------------------------------------------------")


#Declaring 'a' as global tells Python to use the variable from the global scope.
#If a variable is defined both globally and locally with the same name,  local variable shadows the global variable inside the function

a = 1  # Global variable

def f():
    print("f():", a)  # Uses global a

def g():
    a = 2  # Local shadows global
    print("g():", a)
#Modifying Global Variables Inside a Function
def h():
    global a
    a = 3  # Modifies global a
    print("h():", a)

print("global:", a)
f()
print("global:", a)
g()
print("global:", a)
h()
print("global:", a)




# By default, one cannot modify a global variable inside a function without declaring it as global.
# UnboundLocalError: local variable 's' referenced before assignment
def fun():
    global s
    s = s + ' programming'   # Error: Python thinks s is local
    print(s)

s = "I love python "
fun()


print("------------------------------------------------------------")

###############CALCULATOR###########################################
print("""Create a mini calculator where each mathematical operation is implemented " \
as a separate function and a main function controls the program.""")

def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y == 0:
        return "Error: Division by zero is not allowed."
    return x / y

def main():
    while True:
        print("\nSelect operation:")
        print("1. Add")
        print("2. Subtract")
        print("3. Multiply")
        print("4. Divide")
        print("5. Exit")

        choice = input("Enter choice (1/2/3/4/5): ")

        if choice == '5':
            print("Exiting the calculator.")
            break

        if choice in ['1', '2', '3', '4']:
            num1 = float(input("Enter first number: "))
            num2 = float(input("Enter second number: "))

            if choice == '1':
                print(f"{num1} + {num2} = {add(num1, num2)}")
            elif choice == '2':
                print(f"{num1} - {num2} = {subtract(num1, num2)}")
            elif choice == '3':
                print(f"{num1} * {num2} = {multiply(num1, num2)}")
            elif choice == '4':
                result = divide(num1, num2)
                print(f"{num1} / {num2} = {result}")
        else:
            print("Invalid input. Please try agn.")

if __name__ == "__main__":
    main()
###############CALCULATOR###########################################  
print("------------------------------------------------------------")    
