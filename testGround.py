data = {
    "carName" : "Tesla",
    "model" : "Model S"
}

block:dict = {}

for item in data:
    block.setdefault(item.__str__(), data.get(item.__str__()))


print(block)