import charge_utils
import storage_utils

SLEEP_INTERVAL = 0.1
MIN_X = -900
MAX_X = 900
MIN_Y = -900
MAX_Y = 900
MOVE_DEFAULT_COST = 0.1
SCAN_BASE_COST = 0.5
DEFAULT_THROTTLE = 0.5
GO_HOME_THRESHOLD = .8
COSTS_KEY = "rover_costs"
MOVE_CATEGORY = "move"
DRILL_CATEGORY = "drill"
DRILL_DEFAULT_MATERIAL_FACTOR = 0.25
DRILL_MATERIAL_MAP = {
    "iron_ore": 0.25,
}
DRILL_SITE_TYPE = "mineral"

planet = get_component("nocturna").id
journal = get_component("journal")


class FakeNotebook:
    def __init__(self):
        self.values = {}

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value

    def has(self, key):
        return key in self.values

    def transaction(self, key, default, updater):
        self.values[key] = updater(self.values.get(key, default))


class RoverHandler:
    def __init__(self, rover):
        self._notebook = FakeNotebook()
        self.charger = charge_utils.ChargeRequester(rover.id)
        self.rover = rover

    def getNotebook(self):
        if isinstance(self._notebook, FakeNotebook):
            notebook = get_component("notebook")
            if notebook:
                #TODO: update values to include local-only samples
                self._notebook = notebook
        return self._notebook

    def getCost(self, category, key, default):
        notebook = self.getNotebook()
        costs = notebook.get(COSTS_KEY, {})
        return costs.get(category, {}).get(key, {}).get("value", default)

    def updateCost(self, category, key, sample):
        notebook = self.getNotebook()
        def updateHelper(costs):
            if category not in costs:
                costs[category] = {}
            if key not in costs[category]:
                costs[category][key] = {}
            value = costs[category][key].get("value", 0)
            count = costs[category][key].get("count", 0)
            value *= count
            value += sample
            count += 1
            value /= count
            costs[category][key]["value"] = value
            costs[category][key]["count"] = count
            return costs
        notebook.transaction(COSTS_KEY, {}, updateHelper)

    def moveBaseCost(self):
        return self.getCost(MOVE_CATEGORY, self.rover.id, MOVE_DEFAULT_COST)

    def updateMoveCost(self, sample):
        self.updateCost(MOVE_CATEGORY, self.rover.id, sample)

    def moveCost(self, x, y):
        return self.moveBaseCost() * self.rover.nav.get_distance_to(x, y)

    def goHomeCost(self, x, y):
        return self.moveBaseCost() * sqrt(x * x + y * y)

    def waitForCharge(self):
        while self.rover.battery.level() < 1:
            sleep(SLEEP_INTERVAL)
        self.charger.cancelCharge()

    def requestCharge(self):
        if self.rover.rescue_status() in ("charging", "outbound"):
            return
        self.charger.requestCharge()

    def _recoveryIntercept(self, x, y):
        pos = self.rover.nav.get_position()
        if x == pos.x:
            return (x, 0)
        if y == pos.y:
            return (0, y)
        slope = (y - pos.y) / (x - pos.x)
        offset = pos.y - pos.x * slope
        xInt = -offset / (slope + 1 / slope)
        yInt = xInt * slope + offset
        return (xInt, yInt)

    def _recoveryAhead(self, x, y):
        (xInt, yInt) = self._recoveryIntercept(x, y)
        if self.rover.nav.get_distance_to(xInt, yInt) < 1:
            return False
        pos = self.rover.nav.get_position()
        if (xInt > pos.x) and (x > pos.x):
            return True
        if (xInt < pos.x) and (x < pos.x):
            return True
        return (yInt > pos.y) == (y > pos.y)
    
    def moveTo(self, x, y, throttle=DEFAULT_THROTTLE):
        dist = self.rover.nav.get_distance_to(x, y)
        if dist <= 0:
            self.rover.nav.brake()
            return
        batteryBefore = self.rover.battery.wh()
        self.rover.nav.set_target(x, y)
        self.rover.nav.set_throttle(throttle)
        gotCharge = False
        while self.rover.nav.get_distance_to(x, y) > 0:
            sleep(SLEEP_INTERVAL)
            status = self.rover.rescue_status()
            if (
                (status == "charging") or
                (status == "outbound" and not self._recoveryAhead(x, y))
            ):
                self.rover.nav.brake()
                self.waitForCharge()
                gotCharge = True
            elif self.rover.nav.throttle() < throttle:
                self.rover.nav.set_target(x, y)
                self.rover.nav.set_throttle(throttle)
        self.rover.nav.brake()
        batteryUsed = batteryBefore - self.rover.battery.wh()
        if (throttle == DEFAULT_THROTTLE) and (not gotCharge):
            cost = batteryUsed / dist
            self.updateMoveCost(cost)

    def goHome(self, *args, **kwargs):
        self.moveTo(0, 0, *args, **kwargs)

    def batteryAwareMove(self, x, y, *args, **kwargs):
        deficit = self.moveCost(x, y) - self.rover.battery.wh()
        if deficit <= 0:
            self.moveTo(x, y, *args, **kwargs)
            return
        if self.moveCost(0, 0) <= self.rover.battery.wh():
            homeDeficit = self.goHomeCost(x, y) - self.rover.battery.capacity()
            if homeDeficit < deficit * GO_HOME_THRESHOLD:
                self.goHome(*args, **kwargs)
                self.waitForCharge()
                self.moveTo(x, y, *args, **kwargs)
                return
        self.requestCharge()
        self.moveTo(x, y, *args, **kwargs)


class ScanRoverHandler(RoverHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scanPoints = None
    
    def scanCost(self):
        return SCAN_BASE_COST * self.rover.sonar.hardness_limit()

    def getScanPoints(self):
        if self._scanPoints:
            return self._scanPoints
        range = self.rover.sonar.range()
        vertInc = floor(1.5 * range)
        horzOffset = floor(sqrt(3) * 0.5 * range)
        horzInc = horzOffset * 2
        evenLeft = horzInc * ceil(MIN_X / horzInc)
        evenRight = horzInc * floor(MAX_X / horzInc)
        oddLeft = horzInc * ceil((MIN_X + horzOffset) / horzInc) - horzOffset
        oddRight = horzInc * floor((MAX_X) / horzInc) + horzOffset
        x = 0
        y = 0
        self._scanPoints = []
        while True:
            while x > MIN_X:
                self._scanPoints.append((x, y))
                x -= horzInc
            self._scanPoints.append((MIN_X, y))
            if y >= MAX_Y:
                break
            y += vertInc
            if y >= MAX_Y:
                y = MAX_Y
            self._scanPoints.append((MIN_X, y))
            x = oddLeft
            while x < MAX_X:
                self._scanPoints.append((x, y))
                x += horzInc
            self._scanPoints.append((MAX_X, y))
            if y >= MAX_Y:
                break
            y += vertInc
            if y > MAX_Y:
                y = MAX_Y
            self._scanPoints.append((MAX_X, y))
            x = evenRight
        x = horzInc
        y = 0
        while True:
            while x < MAX_X:
                self._scanPoints.append((x, y))
                x += horzInc
            self._scanPoints.append((MAX_X, y))
            if y <= MIN_Y:
                break
            y -= vertInc
            if y <= MIN_Y:
                y = MIN_Y
            self._scanPoints.append((MAX_X, y))
            x = oddRight
            while x > MIN_X:
                self._scanPoints.append((x, y))
                x -= horzInc
            self._scanPoints.append((MIN_X, y))
            if y <= MIN_Y:
                break
            y -= vertInc
            if y < MIN_Y:
                y = MIN_Y
            self._scanPoints.append((MIN_X, y))
            x = evenLeft
        return self._scanPoints

    def scanAt(self, x, y, full=True, *args, **kwargs):
        self.batteryAwareMove(x, y, *args, **kwargs)
        cost = self.scanCost()
        if self.rover.battery.wh() < cost:
            self.requestCharge()
            while self.rover.battery.wh() < cost:
                sleep(SLEEP_INTERVAL)
        sites = self.rover.sonar.scan().sites
        if full and sites:
            if self.rover.battery.wh() < cost * len(sites):
                self.requestCharge()
            for site in sites:
                while self.rover.battery.wh() < cost:
                    sleep(SLEEP_INTERVAL)
                self.rover.sonar.survey(site.id)


class DrillRoverHandler(RoverHandler):
    __DRILL_COST_MAP = {
        1: 10,
        3: 20,
        4: 30,
    }
    def drillBaseCost(self):
        return self.__DRILL_COST_MAP.get(self.rover.drill.hardness_limit(), 10)

    def drillMaterialFactor(self, material):
        default = DRILL_MATERIAL_MAP.get(material, DRILL_DEFAULT_MATERIAL_FACTOR)
        return self.getCost(DRILL_CATEGORY, material, default)

    __PURITY_MAP = {
        "standard": 1,
        "rich": 2,
        "pure": 3,
    }
    def drillPurityDivisor(self, purity):
        return self.__PURITY_MAP.get(purity, 1)

    def drillCost(self, site):
        baseCost = self.drillBaseCost()
        materialFactor = self.drillMaterialFactor(site.item_id)
        speedFactor = self.rover.drill.speed_multiplier()
        purityDivisor = self.drillPurityDivisor(site.purity)
        return baseCost * materialFactor * speedFactor / purityDivisor

    def updateMaterialFactor(self, site, sample):
        baseCost = self.drillBaseCost()
        speedFactor = self.rover.drill.speed_multiplier()
        purityDivisor = self.drillPurityDivisor(site.purity)
        adjustFactor = baseCost * speedFactor / purityDivisor
        sample /= adjustFactor
        self.updateCost(DRILL_CATEGORY, site.item_id, sample)

    def getMiningSite(self, x, y):
        nearest = None
        nearestD2 = 0
        for site in journal.surveyed_sites(planet):
            if site.kind() != DRILL_SITE_TYPE:
                continue
            if (site.x == x) and (site.y == y):
                return site
            dx = site.x - x
            dy = site.y - y
            dSquared = (dx * dx) + (dy * dy)
            if (not nearest) or (dSquared < nearestD2):
                nearest = site
                nearestD2 = dSquared
        return nearest

    def getMiningSites(self):
        allSites = {}
        for site in journal.surveyed_sites(planet):
            if site.kind() != DRILL_SITE_TYPE:
                continue
            dSquared = (site.x * site.x) + (site.y * site.y)
            cargoFree = (rover.cargo.capacity() - rover.cargo.count())
            costPerDrill = self.drillCost(site)
            cost = costPerDrill * cargoFree
            cost += self.moveCost(site.x, site.y)
            cost += self.goHomeCost(site.x, site.y)
            if site.item_id not in allSites:
                allSites[site.item_id] = []
            allSites[site.item_id].append((cost, dSquared, site))
        sites = {}
        for mineral in allSites.keys():
            allSites[mineral].sort()
            sites[mineral] = allsites[mineral][0][2]
        return sites

    def storeCargo(self):
        for item in self.rover.cargo.stacks():
            storageName = storage_utils.formatStorage(item.id)
            storage_utils.connectStorageName(self.rover.output, storageName)
            toSend = item.count
            while toSend > 0:
                result = self.rover.output.send(item.id, toSend)
                if result.status in ("ok", "partial"):
                    toSend -= result.moved
        self.rover.output.connect("")

    def mineAt(self, site):
        if not self.rover.cargo.full():
            self.moveTo(site.x, site.y)
        homeCost = self.moveCost(0, 0)
        while not self.rover.cargo.full():
            drillCost = self.drillCost(site)
            toDrill = self.rover.cargo.capacity() - self.rover.cargo.count()
            if self.rover.battery.wh() < toDrill * drillCost + homeCost:
                self.requestCharge()
            gotCharge = (self.rover.rescue_status() == "charging")
            batteryBefore = self.rover.battery.wh()
            result = self.rover.drill.mine()
            batteryUsed = batteryBefore - self.rover.battery.wh()
            if self.rover.rescue_status() == "charging":
                gotCharge = True
            if result.status in ("no_power", "not_enough_power"):
                while self.rover.battery.wh() < self.drillCost(site):
                    sleep(SLEEP_INTERVAL)
            elif result.status == "busy":
                sleep(SLEEP_INTERVAL)
                continue
            elif result.status != "ok":
                break
            self.updateMaterialFactor(site, batteryUsed)
        self.goHome()
        self.storeCargo()