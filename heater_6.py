MIN_POWER = 0
MAX_POWER = 10

optimalSettings = {}

def setOptimal():
    state = self.thermal_state()
    if state in optimalSettings:
        self.set_power(optimalSettings[state])
        return
    maxEfficiency = 0
    maxEffPower = 0
    for power in range(MIN_POWER, MAX_POWER + 1):
        if self.thermal_state() != state:
            return
        self.set_power(power)
        efficiency = self.efficiency()
        if efficiency >= 100:
            optimalSettings[state] = power
            return
        if efficiency > maxEfficiency:
            maxEfficiency = efficiency
            maxEffPower = power
    self.set_power(maxEffPower)

while True:
    setOptimal()