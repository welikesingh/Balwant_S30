
print('-----------------------------------------------------------------------------')
print("2.---Banking Application---")
print(""" Create a menu-driven banking program supporting
          Check balance
          Deposit
          Withdraw
          Transaction history
          Exit  
          Use functions for each operation and while for the application menu.""")

balance=1000 # Initialization
def check_balance():
    return balance

def deposit_amt():
    try:
        amount = float(input("Enter deposit amount: "))
        global balance 
        balance = check_balance() + amount
        print(f"Amount ${amount} deposited successfully.")
        print("New balance:", balance)
    except Exception as e:
        print("User entered invalid amount. Error: ", e)

def withdraw_amt():
    try:
        amount = float(input("Enter withdrawal amount: "))
        global balance
        if amount <= balance:
            balance = balance - amount
            print(f"Please collect your cash.{amount}")
            print("Remaining balance:", balance)
        else:
            print("Insufficient balance.")
    except Exception as e:
        print("User entered invalid amount to withdraw. Error: ", e)
    
def display_menu():
    print("\n--- MENU ---")
    print("Please select option: ")
    print("Enter 1: To check Balance ")
    print("Enter 2: To Deposit Money ")
    print("Enter 3: To Withdraw money ")
    print("Enter exit: To exit from System ")

while True:
    display_menu()
    choice = input("Enter your choice : ")
    if choice == "1":
        print("Your current balance is:", check_balance())
    elif choice == "2":
        deposit_amt()        
    elif choice == "3":
        withdraw_amt()
    elif choice.upper() == "EXIT":
        print("Thank you for using the ATM. Goodbye!")
        break
    else:
        print("Invalid choice. Please select between 1 and 4.")
   
print('-----------------------------------------------------------------------------')
