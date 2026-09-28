CHANNEL = "charge"
SLEEP_INTERVAL = 0.1
MAX_SKIPS = 3

fleet = get_component("fleet")


class ChargeRequester:
    def __init__(self, vehicle):
        self.vehicle = vehicle
        self._comms = None
        self._request = None

    def getComms(self):
        if not self._comms:
            self._comms = get_component("comms")
        return self._comms

    def requestCharge(self):
        comms = self.getComms()
        while not comms:
            sleep(SLEEP_INTERVAL)
            comms = self.getComms()
        if self._request:
            for msg in comms.pending(CHANNEL):
                if msg.id == self._request:
                    return
        result = comms.send(CHANNEL, self.vehicle)
        while result.status != "ok":
            sleep(SLEEP_INTERVAL)
            result = comms.send(CHANNEL, self.vehicle)
        self._request = result.message_id

    def cancelCharge(self):
        if not self._request:
            return
        comms = self.getComms()
        if not comms:
            return
        comms.cancel(CHANNEL, self._request)
        self._request = None


def hasCharger(outpost):
    return bool(outpost.buildings("charging_station"))

def getChargerSites():
    network = get_component("outpost_network")
    return [outpost for outpost in network.outposts() if hasCharger(outpost)]


class ChargerHandler:
    def __init__(self, charger):
        self.charger = charger
        self.x = charger.outpost.x
        self.y = charger.outpost.y
        self._comms = None
        self.skips = {}
        self.queue = []

    def getComms(self):
        if not self._comms:
            self._comms = get_component("comms")
        return self._comms

    def chargeNearby(self):
        for vehicleId in self.charger.get_docked():
            if vehicleId in self.charger.get_queue():
                continue
            vehicle = get_component(vehicleId)
            if (vehicle.battery.level() >= 1) or (vehicle.battery.capacity() <= 0):
                continue
            self.charger.charge(vehicleId)

    def _chargeRemoteRequest(self):
        comms = self.getComms()
        if not comms:
            return False
        pending = set(msg.id for msg in comms.pending(CHANNEL))
        prune = set(self.skips.keys()).difference(pending)
        for msgId in prune:
            del self.skips[msgId]
        chargers = getChargerSites()
        for msg in comms.pending(CHANNEL):
            vehicleId = msg.value
            vehicle = get_component(vehicleId)
            if vehicle.rescue_status() in ("outbound", "charging"):
                print(f"Ignoring charge for {vehicleId}; rescue already enroute")
                continue
            pos = vehicle.nav.get_position()
            dx = self.x - pos.x
            dy = self.y - pos.y
            dSquared = (dx * dx) + (dy * dy)
            gotCloser = False
            for charger in chargers:
                dx = charger.x - pos.x
                dy = charger.y - pos.y
                if (dx * dx) + (dy * dy) < dSquared:
                    gotCloser = True
                    break
            if gotCloser:
                skipCount = self.skips.get(msg.id, 0)
                if skipCount < MAX_SKIPS:
                    print(f"Skipping {vehicleId}; closer station should handle")
                    self.skips[msg.id] = skipCount + 1
                    continue
            msg = comms.receive(CHANNEL, msg.id)
            if msg.status == "ok":
                print(f"Handling requested charge for {vehicleId}")
                self.charger.dispatch_rescue(msg.packet.value)
                return True
        return False

    def chargeRemote(self):
        if self.charger.is_rescuing():
            return
        if self._chargeRemoteRequest():
            return
        if not self.queue:
            vehicles = [v for v in fleet.vehicles() if v.battery_level <= 0]
            vehicles.sort(key=lambda v: ((v.x - self.x) * (v.x - self.x)) + ((v.y - self.y) * (v.y - self.y)))
            self.queue = [v.id for v in vehicles]
        while self.queue:
            vehicleId = self.queue.pop(0)
            vehicle = get_component(vehicleId)
            if vehicle.rescue_status() in ("outbound", "charging"):
                continue
            if (vehicle.battery.level() >= 1) or (vehicle.battery.capacity() <= 0):
                continue
            self.charger.dispatch_rescue(vehicleId)
            return

    def chargeLoop(self):
        while True:
            self.chargeNearby()
            self.chargeRemote()
            sleep(SLEEP_INTERVAL)
