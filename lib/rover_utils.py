import charge_utils

SLEEP_INTERVAL = 0.1
DEFAULT_THROTTLE = 0.5
CHARGER_THRESHOLD = .8
HEAVY_MODULES = set([
    "nav_module",
    "nav_module_sport",
    "drill_module",
    "drill_module_industrial",
    "drill_module_heavy",
    "sonar_module",
    "sonar_module_wide",
    "sonar_module_deep",
    "constructor_module",
])
BASE_CONSUMPTION = 3
HEAVY_MODULE_CONSUMPTION = 8
CARGO_CONSUMPTION = 0.04
SPORT_CONSUMPTION = 1.3
BASE_SPEED = 100


class RoverHandler:
    def __init__(self, rover, defaultThrottle=DEFAULT_THROTTLE):
        self.charger = charge_utils.ChargeRequester(rover.id)
        self.rover = rover
        self.defaultThrottle = defaultThrottle

    def moveBaseCost(self, throttle, cargo=None):
        if cargo is None:
            cargo = self.rover.cargo.count()
        cost = BASE_CONSUMPTION
        for module in self.rover.modules():
            if module.module_id in HEAVY_MODULES:
                cost += HEAVY_MODULE_CONSUMPTION
        cost += cargo * CARGO_CONSUMPTION
        cost *= sqrt(throttle)
        speedMult = self.rover.nav.speed_multiplier()
        if speedMult > 1:
            cost *= SPORT_CONSUMPTION
        maxSpeed = BASE_SPEED * speedMult
        return cost / maxSpeed

    def moveCost(self, x, y, throttle=None, fromX=None, fromY=None, cargo=None):
        distance = self.rover.nav.get_distance_to(x, y)
        if (fromX is not None) and (fromY is not None):
            dx = fromX - x
            dy = fromY - y
            distance = sqrt((dx * dx) + (dy * dy))
        if throttle is None:
            throttle = self.defaultThrottle
        return self.moveBaseCost(throttle, cargo) * distance

    def waitForCharge(self):
        while self.rover.battery.level() < 1:
            sleep(SLEEP_INTERVAL)
        self.charger.cancelCharge()

    def requestCharge(self):
        if self.rover.rescue_status() in ("charging", "outbound"):
            return
        self.charger.requestCharge()
    
    def moveTo(self, x, y, throttle=None):
        if throttle is None:
            throttle = self.defaultThrottle
        dist = self.rover.nav.get_distance_to(x, y)
        if dist <= 0:
            self.rover.nav.brake()
            return
        if self.rover.battery.wh() <= self.moveCost(x, y, throttle):
            print("Requesting charge")
            self.requestCharge()
        self.rover.nav.set_target(x, y)
        self.rover.nav.set_throttle(throttle)
        while self.rover.nav.get_distance_to(x, y) > 0:
            sleep(SLEEP_INTERVAL)
            if self.rover.rescue_status() == "charging":
                self.rover.nav.brake()
                self.waitForCharge()
                print("Got requested charge")
            elif self.rover.nav.throttle() < throttle:
                self.rover.nav.set_target(x, y)
                self.rover.nav.set_throttle(throttle)
        self.rover.nav.brake()

    def chargerAwareMove(self, x, y, throttle=None, *args, **kwargs):
        deficit = self.moveCost(x, y, throttle) - self.rover.battery.wh()
        if deficit <= 0:
            self.moveTo(x, y, throttle, *args, **kwargs)
            return
        bestCharger = None
        minDeficit = None
        for charger in charge_utils.getChargerSites():
            if self.moveCost(charger.x, charger.y, throttle) >= self.rover.battery.wh():
                continue
            chDeficit = self.moveCost(x, y, throttle, charger.x, charger.y) - self.rover.battery.capacity()
            if (minDeficit is None) or (chDeficit < minDeficit):
                bestCharger = charger
                minDeficit = chDeficit
        if (minDeficit is not None) and (minDeficit < deficit * CHARGER_THRESHOLD):
            print("Going to base to charge")
            self.moveTo(bestCharger.x, bestCharger.y, throttle, *args, **kwargs)
            self.waitForCharge()
        else:
            print("Not going to make it to destination; requesting charge")
            self.requestCharge()
        self.moveTo(x, y, throttle, *args, **kwargs)
