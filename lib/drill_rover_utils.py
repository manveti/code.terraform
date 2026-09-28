import cargo_rover_utils
import storage_utils

SLEEP_INTERVAL = 0.1
DRILL_DEFAULT_MATERIAL_FACTOR = 0.25
DRILL_MATERIAL_MAP = {
    "cobalt": 0.3333333333333333,  # 20 mins
    "iron_ore": 0.25,  # 15 mins
    "lead_ore": 0.3,  # 18 mins
    "neutronium": 0.5,  # 30 mins
    "rare_earth": 0.4166666666666667,  # 25 mins
    "silicon": 0.25,  # 15 mins
    "titanium": 0.3333333333333333,  # 20 mins
}
DRILL_COST_MAP = {
    1: 10,
    3: 20,
    4: 30,
}
PURITY_MAP = {
    "standard": 1,
    "rich": 2,
    "pure": 3,
}
DRILL_SITE_TYPE = "mineral"

journal = get_component("journal")


class DrillRoverHandler(cargo_rover_utils.CargoRoverHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.planetId = get_component("gps").planet().id

    def drillMaterialFactor(self, material):
        return DRILL_MATERIAL_MAP.get(material, DRILL_DEFAULT_MATERIAL_FACTOR)

    def drillBaseCost(self):
        return DRILL_COST_MAP.get(self.rover.drill.hardness_limit(), 10)

    def drillPurityDivisor(self, purity):
        return PURITY_MAP.get(purity, 1)

    def drillCost(self, site):
        baseCost = self.drillBaseCost()
        materialFactor = self.drillMaterialFactor(site.item_id)
        speedFactor = self.rover.drill.speed_multiplier()
        purityDivisor = self.drillPurityDivisor(site.purity)
        return baseCost * materialFactor * speedFactor / purityDivisor

    def printMaterialFactor(self, site, sample):
        baseCost = self.drillBaseCost()
        speedFactor = self.rover.drill.speed_multiplier()
        purityDivisor = self.drillPurityDivisor(site.purity)
        adjustFactor = baseCost * speedFactor / purityDivisor
        sample /= adjustFactor
        print(f"Drilled {site.item_id} with factor {sample}")

    def getMiningSite(self, x, y):
        nearest = None
        nearestD2 = 0
        for site in journal.surveyed_sites(self.planetId):
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

    def mineAt(self, site, homeCost=0):
        if (type(site) in (type(()), type([]))) and (len(site) == 2):
            site = self.getMiningSite(*site)
        self.moveTo(site.x, site.y)
        drillCost = self.drillCost(site)
        while not self.rover.cargo.full():
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
                self.requestCharge()
                while self.rover.battery.wh() < self.drillCost(site):
                    sleep(SLEEP_INTERVAL)
            elif result.status == "busy":
                sleep(SLEEP_INTERVAL)
                continue
            elif result.status != "ok":
                break
            if not gotCharge:
                self.printMaterialFactor(site, batteryUsed)

    def mineLoop(self, site, outpost):
        if (type(site) in (type(()), type([]))) and (len(site) == 2):
            site = self.getMiningSite(*site)
        outpost = storage_utils.getOutpost(outpost)
        fullCargo = self.rover.cargo.capacity()
        homeCost = self.moveCost(site.x, site.y, fromX=outpost.x, fromY=outpost.y, cargo=fullCargo)
        while True:
            self.mineAt(site, homeCost)
            self.deliverTo(outpost, site.item_id)
            while self.rover.cargo.count() > 0:
                sleep(SLEEP_INTERVAL)
                self.deliverTo(outpost, site.item_id)
            self.waitForCharge()
