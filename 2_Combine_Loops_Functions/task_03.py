print("3.---Inventory Management---")
print("""Maintain products containing
            product name
            price
            quantity
        Provide functions to
            add product
            display products
            search product
            update quantity
        calculate total inventory value""")

products=[]
def add_product():
    prd_name=input("Enter Product Name: ")
    price=float(input("Enter Product Price: "))
    qty=float(input("Enter Quantity: "))
    prod_dict={
            "ProductName": prd_name,
            "Price":price,
            "Quantity": qty
            }
    products.append(prod_dict)
    print(f"Added '{prd_name}' successfully.")

def display_product():
    if not products:
            print("Inventory is empty.")
            return
    for p in products:
            print(f"Product Name: {p['ProductName']} | Price: ${p['Price']:.2f} | Quantity: {p['Quantity']}")
    print("-" * 25)

def search_prod():
    prod_name = input("Enter product name that you want to search: ")
    # Search for a product by name
    for p in products:
        if p['ProductName'].lower() == prod_name.lower():
            print(f"Found: Product Name: {p['ProductName']} | Price: ${p['Price']:.2f} | Quantity: {p['Quantity']}")
            return p
    print(f"Product '{prod_name}' not found.")
    return None


def update_quantity():
    prod_name = input("Enter product name : ")
    new_quantity= int(input("Enter product Quantity to update: "))
    # Update the quantity of an existing product
    for p in products:
        if p['ProductName'].lower() == prod_name.lower():
            p['Quantity'] = new_quantity
            print(f"Updated quantity for '{p['ProductName']}' to new Qty {new_quantity}.")
            return
    print(f"Product '{prod_name}' not found.")

def calculate_total_value(self):
    # Calculate total value of all items in inventory
    total = sum(p['price'] * p['quantity'] for p in self.products)
    print(f"Total Inventory Value: ${total:.2f}")
    return total



def display_menu():
    print("\n--- MENU ---")
    print("Please select option: ")
    print("Enter 1: Add Product ")
    print("Enter 2: Display Product ")
    print("Enter 3: Search Product ")
    print("Enter 4: Update Quantity ")
    print("Enter exit/5: To exit from System ")

while True:
    display_menu()
    choice = input("Enter your choice : ")
    if choice == "1":
        add_product()

    elif choice == "2":
        display_product()  

    elif choice == "3":
        search_prod()

    elif choice == "4":
        update_quantity()

    elif choice.upper() in ("5", "EXIT"):
        print("Existing Goodbye!")
        break
    else:
        print("Invalid choice. Please select between 1 and 5.")

