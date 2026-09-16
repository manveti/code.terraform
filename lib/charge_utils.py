CHANNEL = "charge"
SLEEP_INTERVAL = 0.1

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


class ChargerHandler:
    def __init__(self, charger):
        self.charger = charger
        self.lastIdx = -1
        self._comms = None
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

    def chargeRemote(self):
        if self.charger.is_rescuing():
            return
        comms = self.getComms()
        if comms:
            msg = comms.receive(CHANNEL)
            if msg.status == "ok":
                self.charger.dispatch_rescue(msg.packet.value)
                return
        if not self.queue:
            self.queue = [v.id for v in fleet.vehicles() if v.battery_level <= 0]
        while self.queue:
            vehicleId = self.queue.pop(0)
            vehicle = get_component(vehicleId)
            if (vehicle.battery.level() >= 1) or (vehicle.battery.capacity() <= 0):
                continue
            self.charger.dispatch_rescue(vehicleId)
            return

    def chargeLoop(self):
        while True:
            self.chargeNearby()
            self.chargeRemote()
            sleep(SLEEP_INTERVAL)