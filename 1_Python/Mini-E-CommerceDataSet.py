#Create a Mini E-Commerce Dataset

products = [
                {
                "name": "Laptop",
                "price": 70000,
                "brand": "Dell"
                },
                {
                "name": "Phone",
                "price": 40000,
                "brand": "Samsung"
                },
                {
                "name": "Tablet",
                "price": 30000,
                "brand": "Apple"
                }
        ]


# argument unpacking (*)
# *products → unpacks the list into individual dictionary arguments.
# print(*products, sep="\n")  # sperator is just to display each element in new line

print("Print All products: ",
    products[0]["name"],
    products[1]["name"],
    products[2]["name"],
    sep="\n" )


print("Print first product :" , products[0]["name"])
print("Print second product's price :", products[1]['price'])
print("Print third product's brand :", products[2]['brand'])
print("Change first product's price :")
products[0]["price"] = 90000
print(products[0])

print("Add rating to the second product :", )
products[1]["rating"] = 2
print(products)

print("Add another product manually :")
products.append({'name': 'Car', 'price': 50000, 'brand': 'Nissan'})

print("Print the final dataset :",products)


# # Explain the combination of
print("""
# List
# Dictionary
# Indexing
# Keys
# Values
# List: An ordered, numbered sequence of items enclosed in square brackets [].
# Dictionary: An unordered collection of data stored as pairs, enclosed in curly braces {}.
# Indexing: The numerical position used to find a specific item in a list, starting at 0 for the first item.
# Keys: Unique labels (like names or IDs) used inside a dictionary to look up data instead of using numbers.

# Python dictionaries are indexed, but they are indexed by keys rather than by numerical sequences.
""")
