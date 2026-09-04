
# Build strong fundamentals in iteration using for, range(), strings, lists, tuples, sets, and dictionaries.

print("Write a program to print numbers from 1 to 100 using a for loop.")
for i in range(1,101):
  print(i)
print("------------------------------------------------------------")

print("Print all even numbers from 1 to 100.")
for i in range(1,101):
  if i%2==0:
    print(i)
print("------------------------------------------------------------")

print("Print all odd numbers from 1 to 100.")

for i in range(1,101):
  if i%2 != 0:
    print(i)
print("------------------------------------------------------------")

print("Take an integer n and print its multiplication table from 1 to 20.")
input_num = int(input("Enter number:"))
for i in range(1,21):
  print(f"{input_num}*{i} = ",input_num*i)   

print("------------------------------------------------------------")

print("Calculate the sum of numbers from 1 to n using a loop.")
input_num = int(input("Enter number:"))
sum=0
for i in range(1,input_num+1 ):
  sum=sum+i
print(f"Sum: {sum}")


print("------------------------------------------------------------")
print("Calculate the factorial of a number without using any built-in factorial function.")

input_num = int(input("Enter number:"))
product=1
fact_list = []
for i in range(1,input_num+1):
  product=product*i
  fact_list.append(str(i))
fact_string = " x ".join(fact_list)  
print(f"Factorial: {fact_string} = {product}")

# import math
# print("Factorial using Lib:" ,math.factorial(input_num))
print("------------------------------------------------------------")

print("Print only the numbers divisible by 3.")
numbers = [12, 7, 9, 20, 33, 42, 8, 15]
numbers_divisible=[]
for num in numbers:
    if num%3 ==0:
      numbers_divisible.append(num)
print(numbers_divisible)

print("------------------------------------------------------------")
print("Print every language along with its length.")
languages = ["Python", "Java", "C++", "JavaScript", "Go"]
for lang in languages:
  print(f"{lang}  ",len(lang))


# dict = {}
# for lang in languages:
#   dict[lang] = len(lang)
# for lang, length in dict.items():
#   print(f"{lang}  {length}")
print("------------------------------------------------------------")
print("Iterate through and print every key and value")
student = {
        "name": "Rahul",
        "age": 22,
        "course": "Data Science",
        "city": "Bangalore"
        }
for key,val in student.items():
    print("Key: ",key, ", Value: ",val)

print("------------------------------------------------------------")


print("Count how many vowels exist in a user-provided string.")
p_string='AebBceFst'
vowels = 'aeiouAEIOU'
count = 0
for char in p_string:
    if char in vowels:
        count += 1
print(f"Number of vowels in '{p_string}': {count}")

print("------------------------------------------------------------")
print("Reverse a string using a for loop without using [::-1] or reversed().")
p_string='AebBceFst'
reverse_str=''
for chr in p_string:
    reverse_str=chr+reverse_str
print("Reversed String: ",reverse_str)

print("------------------------------------------------------------")

print("Find the largest number from a list without using max().")
p_list=[2,3,3,4,5,1,0,1,70,3,7]
largest=float('-inf')
for num in p_list:
    if num >largest:
        largest=num
print("Largest Number: ",largest)

print("------------------------------------------------------------")
