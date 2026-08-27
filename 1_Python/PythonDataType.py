#Python Data Type Laboratory
# Create at least 15 different variables 
var1=10
print(type(var1))

var2=10.5
print(type(var2))

var3="Balwant"
print(type(var3))

var4=True
print(type(var4))

var5_list=[1,2,3,4,5,6]
print(type(var5_list))

var6_tuple=(1,2,3,4,5,6)
print(type(var6_tuple))

var7_set={1,2,3,4,5,6}
print(type(var7_set))

var8_dict={
    "name": "Balwant", 
    "City": "Oklahoma",
    "Zip": 73012
}
print(type(var8_dict))

var9="Student stay in colleges"
var10=var9.find("stay")
print(var10, " ", type(var10))

var11=reversed(var9)
print(var11, " ", type(var11))

var12="".join(reversed(var9))
print(var12)

var13=var9[::-1]
print(var13, " ", type(var13) )

var14=chr(97)
print(var14, " ", type(var14) )

var15=ord('z')
