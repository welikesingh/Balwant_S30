# ## Task 4 — E-Commerce Product System

# What to build
# Create a Product class for a small e-commerce application.
# Every product should have product ID, name, price, category, and stock quantity. 
# Implement methods such as display_product(), update_stock() and calculate_total_price(quantity).

# Create a static method
# Product.is_valid_price(price)

# It should return True if the price is greater than zero and False otherwise.
# Create at least 5 different products and demonstrate buying/updating stock.


class Product:
    def __init__(self, productID, name, price, category,stock_quantity):
          if not Product.is_valid_price(price):
            raise ValueError(f"Invalid price: {price}. Price must be greater than zero.")
          self.productID = productID
          self.name = name
          self.price = price
          self.category = category
          self.stock_quantity = stock_quantity
 
    def display_product(self):
          print(f"Product ID: {self.productID}")
          print(f"Name: {self.name}")
          print(f"Price: {self.price}")
          print(f"Category: {self.category}")
          print(f"Stock Quantity: {self.stock_quantity}")
          print('-'*40)

    def update_stock(self, quantity: int):
        new_stock = self.stock_quantity + quantity
        if new_stock < 0:
            raise ValueError(f"Cannot reduce stock by {abs(quantity)}; only {self.stock_quantity} available" )
        self.stock_quantity = new_stock
         
    def calculate_total_price(self, new_quantity):
          if new_quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
          return self.price * new_quantity
          
    #no access to self or cls is required in static case
    @staticmethod
    def is_valid_price(price):
          if price > 0:
               return True
          else:
               return False


# --- create 5 products ---
print("---- create 5 products ----")
p1 = Product("P001", "Wireless Mouse", 799, "Electronics", 50)
p2 = Product("P002", "Notebook", 60, "Stationery", 200)
p3 = Product("P003", "Bluetooth Speaker", 1499, "Electronics", 30)
p4 = Product("P004", "Office Chair", 5999, "Furniture", 15)
p5 = Product("P005", "Water Bottle", 299, "Accessories", 100)

products = [p1, p2, p3, p4, p5]

for p in products:
    p.display_product()

# --- demonstrate buying ---
print("---- demonstrate buying ----")
qty_to_buy = 5
total = p1.calculate_total_price(qty_to_buy)
print(f"Buying {qty_to_buy} x {p1.name} = {total}")


print("----Reduce stock (sale)----")
p1.update_stock(-qty_to_buy)  
print(f"Stock remaining for {p1.name}: {p1.stock_quantity}")


# --- demonstrate restocking ---
print("---- demonstrate restocking ----")
p4.update_stock(10)
print(f"Stock after restock for {p4.name}: {p4.stock_quantity}")


# --- demonstrate validation failures ---
print("---- demonstrate validation failures ----")
try:
    p2.calculate_total_price(500)   # more than available stock
except ValueError as e:
    print("Error:", e)


print("----  Invalid price at creation validation  ----")
try:
    Product("P006", "Broken Item", -10, "Misc", 5)
except ValueError as e:
    print("Error:", e)

print("Direct static call:", Product.is_valid_price(0))   # False
print("Direct static call:", Product.is_valid_price(299)) # True


