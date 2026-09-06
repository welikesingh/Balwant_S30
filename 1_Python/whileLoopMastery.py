# Understand condition-controlled iteration and learn where while is more appropriate than for.

print("----------------------------------------------")
print("Print numbers from 1 to 100 using while.")
i=1 #Initialization
while (i <=100):
    print(i)
    i=i+1 # Updating iterator

print("----------------------------------------------")

print("Print numbers from 100 to 1.")
i=100 #Initiatlization
while (i>=1):
    print(i)
    i=i-1


print("----------------------------------------------")

print("Print all even numbers between 1 and 100.")
i=1 #Initiatlization
while (i<=100):
  if i%2==0:
     print(i)
  i=i+1

print("----------------------------------------------")

print("Calculate the sum of digits of a number.")
num=12345 #Initiatlization
sum=0  #Initiatlization
for i in str(num):
  sum=sum+int(i)
print("Sum: ", sum)


### using while
num=12345 #Initiatlization
sum=0
while num > 0:
    digit = num % 10            # 1. Extract the last digit
    sum += digit                # 2. Add the digit to the total sum
    num = num // 10             # 3. Remove the last digit from the number
print("Sum using while: ",sum)    
   

print("----------------------------------------------")
print("Reverse an integer using a while loop.")
num =123456 #Initiatlization
reversed=''
while num >0:
   last_digit = num % 10
   reversed=reversed+str(last_digit)
   num = num // 10
reversed=int(reversed)
print(type(reversed),' ',reversed)

# another approach
num =123  #Initiatlization
reversed=0
while num >0:
   last_digit = num % 10
   reversed = (reversed * 10) + last_digit  # 2. Append it to the result
   num = num // 10
print(type(reversed),' ',reversed)



print("----------------------------------------------")
print("Count the number of digits in an integer.")
num=1234 #Initiatlization
#print(len(str(num)))
cnt=0
while num > 0:
  cnt+=1
  num=num//10
print("Digits: ",cnt)  
print("----------------------------------------------")

print("Calculate factorial using while.")
num=4 # input number to calculate factorial

fact=1
while num>=1:
  fact=fact*num
  num=num-1
print('Factorial: ',fact)


print("----------------------------------------------")
print("""
Create a program that repeatedly asks for numbers and stops only when the user enters 0. 
Display the sum of all previously entered numbers.
""")
input_num=int(input("Enter input Num(0 to Exit):"))
#print('Entered input: ',input_num)
sum=0
while ( input_num != 0 ):
   sum=sum+input_num
   input_num=int(input("Enter input Num(0 to Exit):"))
   #print('Entered input: ',input_num)
print("Sum: ", sum)   

print("----------------------------------------------")

print("""Create a password checker that keeps asking for the password until 
the correct password is entered.""")
entered_password=input("Enter password: ")
stored_password='welcome1' # Initialization

print("Entered password: ",entered_password)
while( entered_password != stored_password ):
   entered_password=input("Enter correct password: ")
   print("Entered password: ",entered_password)
print("PAssword Authentication is successful")



print("----------------------------------------------")   

print("""Create a guessing game where the secret number is predefined 
and the user keeps guessing until correct.""")
secret_num=9999 #Initialization for secret number

guessed_num=int(input("Please guess a secret num: "))
print("Guessed Number: ",guessed_num)
if guessed_num > secret_num:
   print("Your guess is higher then expected")
elif guessed_num < secret_num:
   print("Your guess is lower then expected")


while( secret_num != guessed_num ):
   guessed_num=int(input("Please guess a secret num: "))
   print("Guessed Number: ",guessed_num)
   if guessed_num > secret_num:
      print("Your guess is higher then expected")
   elif guessed_num < secret_num:
      print("Your guess is lower then expected")

print("Guessed is correct :", guessed_num)


print("----------------------------------------------")  

print("""Build a menu-driven calculator
        1 Add
        2 Subtract
        3 Multiply
        4 Divide
        5 Exit
        """)


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

def main_calculator():
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


## calling main_calculator
main_calculator()




print("----------------------------------------------")  
print("""
Create an ATM menu using while where the application continues running until 
the user explicitly chooses Exit.
""")

balance = 1000 # db value #Initiatlization
def options_display():
    print("\n--- ATM MENU ---")
    print("Please select option: ")
    print("Enter 1: To check Balance ")
    print("Enter 2: To Deposit Money ")
    print("Enter 3: To Withdraw money ")
    print("Enter exit: To exit from System ")

while True:
    options_display()
    choice = input("Enter your choice : ")

    if choice == "1":
        print("Your current balance is:", balance)

    elif choice == "2":
        amount = float(input("Enter deposit amount: "))
        balance = balance + amount
        print("Amount deposited successfully.")
        print("New balance:", balance)

    elif choice == "3":
        amount = float(input("Enter withdrawal amount: "))
        if amount <= balance:
            balance = balance - amount
            print("Please collect your cash.")
            print("Remaining balance:", balance)
        else:
            print("Insufficient balance.")

    elif choice.upper() == "EXIT":
        print("Thank you for using the ATM. Goodbye!")
        break

    else:
        print("Invalid choice. Please select between 1 and 4.")
