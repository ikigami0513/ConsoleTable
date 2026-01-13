from lib import TextTable

users = [
    ["Ethan", 22, "France"],
    ["Amélie", 19, "France"]
]

table = TextTable()

table.add_column("Name", align="left")
table.add_column("Age", align="center")
table.add_column("Country", align="left")

for user in users:
    table.add_row(*user)

output = table.generate()
print(output)
