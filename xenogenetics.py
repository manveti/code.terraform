reference = set(self.contract.earth_ref)
results = []
for seq in self.contract.samples:
    if seq not in reference:
        results.append(seq)
transmitter = get_component("transmitter")
transmitter.connect("earth")
transmitter.transmit(self.contract.id, results)