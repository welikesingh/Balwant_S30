# calculate total transaction value without using sum().
# find the highest and lowest transaction without max() and min().
transactions = [1200, 450, 800, 1500, 2300, 700, 100]
sum=0
highest=transactions[0]
lowest=transactions[0]

for elem in transactions:
    # sum
    sum=sum+elem
    # highest
    if elem > highest:
        highest=elem
    if elem < lowest:
        lowest= elem

print(f"Sum: {sum}", f"Highest: {highest}", f"Lowest: {lowest}", sep='\n')

print("------------------------------------------------------------")


# Find the average temperature.
temperatures = [32, 35, 28, 40, 38, 31, 42]
element_cnt = len(temperatures)
sum=0
for i in temperatures:
    sum=sum+i
print("average temperature: ", sum/element_cnt)   
print("------------------------------------------------------------")

#Given student marks
marks = [78, 92, 45, 67, 88, 53, 99]
# count how many students scored
# 90+
# 75–89
# 50–74
# below 50
marks = [78, 92, 45, 67, 88, 53, 99]

count_90 = 0
count_75_89 = 0
count_50_74 = 0
count_below_50 = 0

for mark in marks:
    if mark >= 90:
        count_90 += 1
    elif mark >= 75:
        count_75_89 += 1
    elif mark >= 50:
        count_50_74 += 1
    else:
        count_below_50 += 1

print("90+ :", count_90)
print("75-89 :", count_75_89)
print("50-74 :", count_50_74)
print("Below 50 :", count_below_50)   




print("------------------------------------------------------------")
# Create a simple login system with a maximum of 3 password attempts.
list_users = [
            {"user":"user1", "password":"password1"},
            {"user":"user2", "password":"password2"},
            {"user":"user3", "password":"password3"},
            {"user":"user4", "password":"password4"}
          ]
l_success='NO'
for i in range(3):
  entered_user= input("Please enter user: ")
  entered_password= input("Enter password: ")
  for lst in list_users:
    if (lst['user'] == entered_user) & (lst['password'] == entered_password):
      l_success='YES'
      print(f"You are successfully logged in {entered_user}!!")
      break
  if l_success != 'YES':
    print("Invalid credentials. Please try again.")
    continue
  else:
    break



print("------------------------------------------------------------")

products = {
            "Laptop": 55000,
            "Phone": 30000,
            "Headphones": 2000,
            "Mouse": 700,
            "Keyboard": 1500
            }

print("print only products costing more than ₹2,000.")
for key, value in products.items():
    if value > 2000:
        print("Product: ",key)


print("------------------------------------------------------------")

print("Accept 10 numbers from the user and store them in a list using a loop.")
list2=[]
for i in range(10):
   inum= int(input("Enter a number: "))
   list2.append(inum)

print(list2)

print("------------------------------------------------------------")

print("Count the frequency of every character in a string without using Counter.")

str='banana'
set2=set(str)
#print(set2)
for i in list(set2):
    print(i,"-->",str.count(i))



print("------------------------------------------------------------")
print("Find the second-largest number in a list without using sort().")
numbers = [2, 4, 5, 6, 6, 8, 8, 3]

largest = float('-inf')
second_largest = float('-inf')

for num in numbers:
    if num > largest:
        second_largest = largest
        largest = num
    elif num > second_largest and num != largest:
        second_largest = num

print("Second largest number is:", second_largest)
print("------------------------------------------------------------")

print("""Create this number pattern
1
12
123
1234
12345
""")

for i in range(1, 6):
    for j in range(1, i + 1):
        print(j, end="")
    print()

    
print("------------------------------------------------------------")


print("Check whether a string is a palindrome using loops.")
s='madam'
i=0
j =len(s) - 1  # last index
is_palindrome = True  

while i < j:
    if s[i] != s[j]:  
        is_palindrome = False
        break
    i += 1
    j -= 1

if is_palindrome:
    print("Yes") 
else:
    print("No") 
print("------------------------------------------------------------")
print("Create a basic ATM simulation where a user can repeatedly")
print("Create a basic ATM simulation where a user can repeatedly")

def options_display():
    print("Please select option: ")
    print("Enter 1: To check Balance ")
    print("Enter 2: To Deposit Money ")
    print("Enter 3: To Withdraw money ")
    print("Enter exit: To exit from System ")

options_display()
ip=input("Choose option ")
print("User selected option: ", ip)
while ip.upper() != 'EXIT':
    if (ip == '1'): 
      print("***Checking Balance processing***")
    elif (ip == '2') :
      print("***Deposit Money processing***")
    elif (ip == '3') :
      print("***Withdraw money processing***")
    else:
      print("***Invalid Option, Please retry***")
    options_display()
    ip=input("Choose option ")
    print("User selected option: ", ip)
print("------------------------------------------------------------")