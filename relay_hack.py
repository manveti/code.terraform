def getCombination():
    combination = {}
    for num in range(0, self.contract.lock.range):
        result = self.contract.lock.intercept([num] * self.contract.lock.tumblers)
        for i in range(len(result)):
            if result[i]:
                combination[i] = num
        if len(combination) >= self.contract.lock.tumblers:
            return [combination[i] for i in range(self.contract.lock.tumblers)]

comb = getCombination()
self.contract.lock.intercept(comb)
trans = get_component("transmitter")
trans.connect("earth")
trans.transmit(self.contract.id, comb)