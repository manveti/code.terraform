samples = [
    list(s) for s in
    (self.contract.broadcast.freq_a, self.contract.broadcast.freq_b, self.contract.broadcast.freq_c)
]
maxLen = max(len(s) for s in samples)
for s in samples:
    l = len(s)
    if l < maxLen:
        s.extend([""] * (maxLen - l))
msg = "".join("".join(t) for t in zip(*samples))
print(msg)
transmitter = get_component("transmitter")
transmitter.connect("earth")
transmitter.transmit(self.contract.id, msg)