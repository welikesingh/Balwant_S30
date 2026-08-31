# Build a Product Dictionary

laptop = {
"brand": "Dell",
"model": "XPS 15",
"price": 120000,
"ram": "16GB",
"storage": "512GB SSD",
"available": True
}

print("Print brand: ", laptop['brand']) 
print("Print model: ", laptop['model']) 
print("Print price: ", laptop['price']) 

print("Change price")
laptop["price"]= 150000
print(laptop["price"])

print("Add processor information")
laptop["processor"]= "iCore 7"
print(laptop)

print("Add GPU information :")
laptop["GPU"]= "AMD R9"
print(laptop)

print("Change RAM to \"32GB\"")
laptop["ram"]= "32GB"
print(laptop)

print("Remove \"available\"")
laptop.pop("available") 


print(" Print all keys :",laptop.keys())
print(" Print all values :", laptop.values())
print(" Print all items :",laptop.items())

print(" Second product dictionary for a mobile phone. :")
mobile={
    "battery": "Lithium",
    "ram": "250GB",
    "touchscreen": True
}
print(mobile)

