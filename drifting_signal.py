def translateChar(c, offset):
    n = ord(c)
    base = ord('A')
    end = ord('Z')
    if (n < base) or (n > end):
        return c
    modulus = end + 1 - base
    n -= base
    return chr(((n + offset) % modulus) + base)

def translateMsg(s, offset):
    return "".join(translateChar(c, offset) for c in s)

#for i in range(26):
#    print(i, translateMsg(self.contract.device.slabs, i))
msg = translateMsg(self.contract.device.slabs, 9)
transmitter = get_component("transmitter")
transmitter.connect("earth")
transmitter.transmit(self.contract.id, msg)