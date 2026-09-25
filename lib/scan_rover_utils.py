import rover_utils

SLEEP_INTERVAL = 0.1
SCAN_BASE_COST = 0.5


class ScanRoverHandler(rover_utils.RoverHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scanPoints = None
    
    def scanCost(self):
        return SCAN_BASE_COST * self.rover.sonar.hardness_limit()

    def getScanPoints(self):
        if self._scanPoints:
            return self._scanPoints
        planet = get_component("gps").planet()
        bounds = planet.get_bounds()
        range = self.rover.sonar.range()
        vertInc = floor(1.5 * range)
        horzOffset = floor(sqrt(3) * 0.5 * range)
        horzInc = horzOffset * 2
        evenLeft = horzInc * ceil(bounds.min_x / horzInc)
        evenRight = horzInc * floor(bounds.max_x / horzInc)
        oddLeft = horzInc * ceil((bounds.min_x + horzOffset) / horzInc) - horzOffset
        oddRight = horzInc * floor(bounds.max_x / horzInc) + horzOffset
        x = 0
        y = 0
        self._scanPoints = []
        while True:
            while x > bounds.min_x:
                self._scanPoints.append((x, y))
                x -= horzInc
            self._scanPoints.append((bounds.min_x, y))
            if y >= bounds.max_y:
                break
            y += vertInc
            if y >= bounds.max_y:
                y = bounds.max_y
            self._scanPoints.append((bounds.min_x, y))
            x = oddLeft
            while x < bounds.max_x:
                self._scanPoints.append((x, y))
                x += horzInc
            self._scanPoints.append((bounds.max_x, y))
            if y >= bounds.max_y:
                break
            y += vertInc
            if y > bounds.max_y:
                y = bounds.max_y
            self._scanPoints.append((bounds.max_x, y))
            x = evenRight
        x = horzInc
        y = 0
        while True:
            while x < bounds.max_x:
                self._scanPoints.append((x, y))
                x += horzInc
            self._scanPoints.append((bounds.max_x, y))
            if y <= bounds.min_y:
                break
            y -= vertInc
            if y <= bounds.min_y:
                y = bounds.min_y
            self._scanPoints.append((bounds.max_x, y))
            x = oddRight
            while x > bounds.min_x:
                self._scanPoints.append((x, y))
                x -= horzInc
            self._scanPoints.append((bounds.min_x, y))
            if y <= bounds.min_y:
                break
            y -= vertInc
            if y < bounds.min_y:
                y = bounds.min_y
            self._scanPoints.append((bounds.min_x, y))
            x = evenLeft
        return self._scanPoints

    def scanAt(self, x, y, *args, **kwargs):
        self.chargerAwareMove(x, y, *args, **kwargs)
        cost = self.scanCost()
        if self.rover.battery.wh() <= cost:
            self.requestCharge()
            while self.rover.battery.wh() < cost:
                sleep(SLEEP_INTERVAL)
        sites = self.rover.sonar.scan().sites
        if self.rover.battery.wh() <= cost * len(sites):
            self.requestCharge()
        for site in sites:
            while self.rover.battery.wh() < cost:
                sleep(SLEEP_INTERVAL)
            self.rover.sonar.survey(site.id)
