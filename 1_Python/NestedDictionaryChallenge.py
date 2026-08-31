# Nested Dictionary Challenge

employee = {
            "name": "Amit",
            "department": "Engineering",
            "skills": {
                        "language": "Python",
                        "database": "PostgreSQL",
                        "cloud": "AWS"
                        },
            "salary": 80000
            }

print("Print employee name: ", employee["name"])

print("Print department :",  employee["department"])
print("Print complete skills dictionary :", employee["skills"])
print("Print programming language :", employee["skills"]["language"])

print("Print database :", employee["skills"]["database"])

print("Print cloud technology :", employee["skills"]["cloud"])

print("Change Python to Python + JavaScript")
employee["skills"]["language"] = employee["skills"]["language"] + "JavaScript"
print(employee["skills"]["language"])

print("Change salary :")
employee["salary"] = 90000
print(employee["salary"])

print("Add \"experience\": ")
employee["experience"] =3
print(employee["experience"])

print("Add another skill under the skills dictionary :")
employee["skills"]["DataLibraries"] = ["pandas","matplot","scikit"]
print(employee)

# Explain how nested dictionaries are accessed.

