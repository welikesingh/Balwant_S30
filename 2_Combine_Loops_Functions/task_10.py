
print('-----------------------------------------------------------------------------')

print("10. ---Expense Tracker---")
print("""Allow a user to repeatedly enter
            expense name
            amount

            Provide options to
            add expense
            view expenses
            calculate total
            find highest expense
            exit

            """)

#Initialise the Expense list
expenses = []

def display_menu():
    print("\n===== EXPENSE TRACKER MENU =====")
    print("1. Add Expense")
    print("2. View Expenses")
    print("3. Calculate Total")
    print("4. Find Highest Expense")
    print("5. Exit")


def add_expense():
    name = input("Enter expense name: ")
    amount = float(input("Enter expense amount: "))
    expense = {
        "name": name,
        "amount": amount
    }
    expenses.append(expense)
    print(f"{name} added successfully!")


def view_expense():
    if len(expenses) == 0:
        print("No expenses found.")
    else:
        print("\n----- EXPENSE LIST -----")
        for expense in expenses:
            print(f"{expense['name']}: ${expense['amount']:.2f}")

def max_expense():    
    if len(expenses) == 0:
        print("No expenses found.")
    else:
        highest = expenses[0]
        for expense in expenses:
            if expense["amount"] > highest["amount"]:
                highest = expense
        print(
            f"\nHighest Expense: "
            f"{highest['name']} - ${highest['amount']:.2f}"
        )


while True:
    display_menu()
    choice = input("Enter your choice (1-5): ")
    # 1. Add Expense
    if choice == "1":
        add_expense()       
    # 2. View Expenses
    elif choice == "2":
        view_expense()
    # 3. Calculate Total
    elif choice == "3":
        total = 0
        for expense in expenses:
            total += expense["amount"]
        print(f"\nTotal Expenses: ${total:.2f}")
    # 4. Find Highest Expense
    elif choice == "4":
        max_expense()
    # 5. Exit
    elif choice == "5":
        print("Thank you for using the Expense Tracker!")
        break
    # Invalid choice
    else:
        print("Invalid choice. Please select a number from 1 to 5.")
print('-----------------------------------------------------------------------------')
