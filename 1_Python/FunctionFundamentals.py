## Learn reusable programming using custom functions, 
# arguments, parameters, return values, and default arguments, doc string

print ("Create def add(a, b) that returns the addition of two numbers. ")
def add(a, b):
    return (a +b)

print(add(5,4))

print("-----------------------------------------------")

print("""Create functions for
addition
subtraction
multiplication
division""")

def math_func(f1: str, a: int, b: int):
    if f1.upper() =='ADD':
        return (a+b)
    if f1.upper() == "SUBTRACT":
        return (a-b)
    if f1.upper() == "MULTIPLY":
        return (a*b)
    if f1.upper() == "DIVIDE":
        return (a/b)        

print('addition: ',math_func('ADD',3,4))
print('subtraction: ',math_func('SUBTRACT',7,4))
print('multiplication: ',math_func('MULTIPLY',3,4))
print('division: ',math_func('DIVIDE',3,4))

print("-----------------------------------------------")

print("Create a function that determines whether a number is even or odd.")
def odd_even(a):
    if a%2==0:
        return ('Even')
    else:
        return ('Odd')

print(odd_even(8))       
print(odd_even(3)) 

print("-----------------------------------------------")

print("Create a function that returns the largest of three numbers without using max().")
def find_largest(a, b, c):
    largest = a
    if b > largest:
        largest = b
    if c > largest:
        largest = c
    return largest

print(find_largest(1,2,3))
print(find_largest(2,1,3))
print(find_largest(1,3,2))    
print(find_largest(3,2,1))
print(find_largest(2,3,1))
print(find_largest(3,1,2))        
print(find_largest(5,5,1))      

print("-----------------------------------------------")

print("Create a function that calculates factorial.")
def fact_fun(a):
   result=1
   for i in range(1,a+1):
      result=result*i
   return result

print(fact_fun(4))
      
print("-----------------------------------------------")

print("Create a function that checks whether a number is prime.")
def is_prime(p):
   #for i in range(2,p):
    for i in range(2,int(p**0.5) + 1): # efficient on iteration
      #print(i)
      if p%i ==0:
        return 'Not Prime'
    return 'Prime'

print(is_prime(13))
print(is_prime(10))

print("-----------------------------------------------")

print("""Create 
def calculate_discount(price, discount=10)
where the default discount is 10%. """)
def calculate_discount(price, discount=10):
   return (price - price*discount/100)

def calculate_discount(price, discount=10):
   return (price - price*discount/100)

print(calculate_discount(10,2))
print(calculate_discount(10))

print("-----------------------------------------------")
print("Create a function that accepts a list and returns its sum without using sum().")
def list_sum(lst: list):
   sum=0
   # print(lst)
   for i in lst:
      sum=sum+i
   return sum

print("List Sum: ",list_sum([1,2,3,4]))
print("-----------------------------------------------")
print("Create a function that accepts a string and returns the number of vowels.")
def count_vowels(input_str):
   vowels='aeiouAEIOU'
   cnt=0
   for chr in input_str:
      if vowels.find(chr) >= 0:
         cnt=cnt+1
   return cnt

print("Number of Vowels: ", count_vowels('This is not just vowels count'))
print("Number of Vowels: ", count_vowels('bbb'))
print("-----------------------------------------------")
print("Create a function that accepts a string and determines whether it is a palindrome.")
def is_palintrome(input_str):
   # Build the string backward
   reversed_text=''
   for char in input_str:
     reversed_text = char + reversed_text
   #(reverse_str)
   if input_str==reversed_text:
     return 'Palindrome'
   else:
     return 'Not Palindrome'
   
print(is_palintrome('madam'))

   
print("-----------------------------------------------")

print("""Create a function that accepts
        name
        age
        course
        and returns a formatted student profile.
        Use both positional and keyword arguments while calling it.""")
def create_student_profile(name,age,course):
    return f"""
   Student Profile
   ---------------
   Name: {name}
   Age: {age}
   Course: {course}
   """

# Calling using positional arguments
print(create_student_profile("John", 22, "Python"))

# Calling using keyword arguments
print(create_student_profile(name="Alice", age=25, course="Data Science"))
print(create_student_profile(age=25, course="Data Science",name="Alice"))

print("-----------------------------------------------")
print("doc string explanation")
#Docstrings (short for "documentation strings") are string literals

def add(a, b):
    """Returns the sum of a and b."""
    return a + b
# design time access using hover over the function
add(1,2)
print(add(1,2))
# Runtime access for doc string
print(add.__doc__)
      
print("-----------------------------------------------")
print("""difference between 
        default argument
        positional argument
        keyword argument""")
def example(a, b=10): 
    print(a,' ',b)

# def example(a=10, b):   # — default can't come before non-default
#     pass

example(20)        # usese default 
example(20,30)     # positional
example(b=30,a=10) # named notation