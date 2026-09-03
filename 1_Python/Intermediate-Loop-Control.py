# Intermediate Loops & Loop Control

print("Print numbers from 1–100 but skip numbers divisible by 5 using continue.")
for i in range(1, 101):
    if i % 5 == 0:
        continue
    print(i)



print("Iterate from 1–100 and stop when you encounter the first number divisible by both 7 and 11.")
for i in range(1, 101):
    if (i % 7 == 0) and (i % 11 == 0):
        print("First number divisible by both 7 and 11 is: ", i)
        break



print("Search for a user-provided number inside a list. Use for-else to print:")
list4=[1,2,3,4,5,6,7,8,9]
user_input = int(input("Enter a number to search in the list: "))
print("Searching for number: ", user_input, "in the list: ", list4)
for num in list4:
    if num == user_input:
        print("Number Found")
        break
else:
    print("Number Not Found")



print("use enumerate() to display indices and values:")
names = ["Aman", "Ravi", "Sudhanshu", "Priya", "Anjali"]
print(list(enumerate(names,start=1)))



print("""Print the following pattern:
*
**
***
****
*****""")
print("---------Printing pattern:---------")
for i in range(1, 6):
    print('*' * i)



print("""Print the following pattern:
*****
****
***
**
*""")
print("------Printing pattern:------")
for i in range(1, 6):
    print('*' * (6-i))




print("Generate multiplication tables from 1 to 10 using nested loops.")
for i in range(1, 11):
    print(f"Multiplication Table for {i}:")
    for j in range(1, 11):
        print(f"{i} x {j} = {i*j}")
    print()  



print("Find all numbers between 1 and 200 divisible by both 3 and 5.")
for i in range(1, 201):
    if (i % 3 == 0) and (i % 5 == 0):
        print(i)    



print("Given a list containing duplicate elements, \n" 
"Create another list containing only unique elements without using set().")
original_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5]
unique_list = []
for item in original_list:
    if item not in unique_list:
        unique_list.append(item)
print("Original List:", original_list)
print("Unique List:", unique_list)




numbers = [10, -4, 8, -2, 0, 15, -9, 21]
print(" Count :", len(numbers))
print("Positive numbers:", len([x for x in numbers if x > 0]))
print("Negative numbers:", len([x for x in numbers if x < 0]))
zeros = [x for x in numbers if x == 0]
print("Count of Zeros:", len(zeros))    




print("Write a program to determine whether a number is prime using a loop.")
n = int(input("Enter a number: "))
#most efficient and common approach is to check for divisors up to the square root of the number
def is_prime_number(num):
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True
if is_prime_number(n):
    print(f"{n} is a prime number.")
else:
    print(f"{n} is not a prime number.")






print("Print all prime numbers between 1 and 100.")
prime_numbers = []
for num in range(1, 101):
    if is_prime_number(num):
        prime_numbers.append(num)
print("Prime numbers between 1 and 100:", prime_numbers)    