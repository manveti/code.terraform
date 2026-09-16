directions = ["south", "east", "north", "west"]
g = {"curDir": 1}

def nextStep():
    g["curDir"] = (g["curDir"] + 3) % 4
    result = self.contract.vault.move(directions[g["curDir"]])
    while result.status == "wall":
        g["curDir"] = (g["curDir"] + 1) % 4
        result = self.contract.vault.move(directions[g["curDir"]])
    return result.status
while nextStep() != "exit":
    pass
key = self.contract.vault.escape()
print(key)
transmitter = get_component("transmitter")
transmitter.connect("earth")
transmitter.transmit(self.contract.id, key.key)