positions = {}
for row in range(self.contract.archive.rows):
    for col in range(self.contract.archive.cols):
        word = self.contract.archive.flip(row, col)
        if word not in positions:
            positions[word] = []
        positions[word] += [row, col]

transmitter = get_component("transmitter")
transmitter.connect("earth")
transmitter.transmit(self.contract.id, positions.values())