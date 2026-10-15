DUMP_THRESHOLD = 50

atmosphere = get_component("atmosphere")

def handleWaste():
    if self.waste() >= DUMP_THRESHOLD:
        self.dump_waste()

def handleIntake():
    co2 = atmosphere.get_co2()
    if co2 < 0:
        co2 = 0
    self.set_intake(co2 / 10)

while True:
    handleWaste()
    handleIntake()