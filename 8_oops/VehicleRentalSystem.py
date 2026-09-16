# Task 6 — Vehicle Rental System

# What to build
# Build a mini vehicle rental application.

# Create a parent Vehicle class containing vehicle number, brand, model, and rental price per day.

# Then create

# Vehicle

# |

# +---- Car

# |

# +---- Bike

# Car can have an additional attribute such as number of seats, while Bike can have engine capacity.

# Create a method

# calculate_rent(days)

# Also create a static method that validates whether the rental duration is valid—for example, the number of rental days must be greater than zero.

# Create at least 2 cars and 2 bikes and demonstrate the complete system.

 

class Vehicle:
    def __init__(self,
                 vehicle_number: str,
                 brand: str,
                 model: str,  
                 rental_price_per_day: float):
            self.vehicle_number= vehicle_number
            self.brand= brand
            self.model= model 
            self.rental_price_per_day= rental_price_per_day # amount 

    def calculate_rent(self, days: int) -> float:
          Vehicle.validate_days(days)  # guard against bad input before doing the math
          return self.rental_price_per_day * days

    def display_details(self):
        print(f"Vehicle Number : {self.vehicle_number}")
        print(f"Brand          : {self.brand}")
        print(f"Model          : {self.model}")
        print(f"Price/Day      : {self.rental_price_per_day}")

    # A static method receives neither self nor cls. 
    # It's just a regular function that happens to live inside the class 
    # for organizational purposes, because it's conceptually related but doesn't need 
    # any information about the class or its instances.
    @staticmethod
    def validate_days(days: int):
        if days <= 0:
            raise ValueError("Rental duration must be greater than zero")

#----Child Class--------------
class Car(Vehicle):
    def __init__(self, vehicle_number, brand, model, rental_price_per_day, num_seats: int):
        super().__init__(vehicle_number, brand, model, rental_price_per_day)  # reuse parent's init
        self.num_seats = num_seats
    # super() reference to the parent class instead of repeating the four assignments in Car and Bike

    def display_details(self):
        # method overriding with extension
        super().display_details()          # print the shared fields first...
        print(f"Seats          : {self.num_seats}")   # ...then the Car-specific one


class Bike(Vehicle):
    def __init__(self, vehicle_number, brand, model, rental_price_per_day, engine_capacity_cc: int):
        super().__init__(vehicle_number, brand, model, rental_price_per_day)
        self.engine_capacity_cc = engine_capacity_cc

    def display_details(self):
        super().display_details()
        print(f"Engine Capacity: {self.engine_capacity_cc}cc")


# --- demonstration ---
car1 = Car("KA01AB1234", "Toyota", "Innova", 2500, num_seats=7)
car2 = Car("KA02CD5678", "Maruti", "Swift", 1200, num_seats=5)

bike1 = Bike("KA03EF9012", "Royal Enfield", "Classic 350", 800, engine_capacity_cc=350)
bike2 = Bike("KA04GH3456", "Honda", "Activa", 400, engine_capacity_cc=110)

vehicles = [car1, car2, bike1, bike2]

for v in vehicles:
    v.display_details()
    print(f"Rent for 3 days: {v.calculate_rent(3)}")
    print("-" * 30)

# demonstrating the validation 
try:
    car1.calculate_rent(0) # It is inheritance
except ValueError as e:
    print("Error:", e)

# static method can also be called directly, without any instance
Vehicle.validate_days(5)   # passes silently — 5 is valid        