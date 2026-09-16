messageChars = []
for row in range(self.contract.tablet.rows):
    for col in range(self.contract.tablet.cols):
        res = self.contract.tablet.probe(row, col)
        if res.distance == 0:
            messageChars.append(res.char)
message = "".join(messageChars)
print(message)
transmitter = get_component("transmitter")
transmitter.connect("earth")
transmitter.transmit(self.contract.id, message)