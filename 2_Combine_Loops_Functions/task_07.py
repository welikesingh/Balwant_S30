
print("7. ---Shopping Cart---")
print("""Create a simple cart where users can
            add products
            remove products
            view cart
            calculate bill
            exit
            The application should continue until Exit is selected.
            """)

cart = {}

# Adding product function
def add_product():    
    product = input("Enter product name: ")
    price = float(input("Enter product price: "))
    quantity = int(input("Enter quantity: "))
    cart[product] = {
        "price": price,
        "quantity": quantity
    }
    print(f"{product} added to cart successfully!")

# Remove product function
def remove_product():
    product = input("Enter product name to remove: ")
    if product in cart:
        del cart[product]
        print(f"{product} removed from cart.")
    else:
        print("Product not found in cart.")

# view cart
def view_cart():
    if len(cart) == 0:
        print("Your cart is empty.")
    else:
        print("\n----- YOUR CART -----")
        for product, details in cart.items():
            print(
                f"Product: {product}, "
                f"Price: ${details['price']}, "
                f"Quantity: {details['quantity']}"
            )

def calculate_bill():
    total_bill = 0
    for product, details in cart.items():
        total_bill += details["price"] * details["quantity"]
    print(f"\nTotal Bill for cart: ${total_bill:.2f}")


while True:
    print("\n===== SHOPPING CART MENU =====")
    print("1. Add Product")
    print("2. Remove Product")
    print("3. View Cart")
    print("4. Calculate Bill")
    print("5. Exit")

    choice = input("Enter your choice (1-5): ")

    # Add Product
    if choice == "1":
       add_product()

    # Remove Product
    elif choice == "2":
        remove_product() 

    # View Cart
    elif choice == "3":
        view_cart()

    # Calculate Bill
    elif choice == "4":
        calculate_bill() 

    # Exit
    elif choice == "5":
        print("Thank you for shopping! Goodbye.")
        break
    else:
        print("Invalid choice. Please select a number from 1 to 5.")
