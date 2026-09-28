import charge_utils
import rover_utils
import storage_utils


class CargoRoverHandler(rover_utils.RoverHandler):
    #TODO: make "thread-safe"; bins and the like are fine, but warehouses have one i/o port for multiple slots
    def loadFromStorage(self, storage, itemId, count=None):
        self.moveTo(storage.x, storage.y)
        if (count is None) or (count > storage.count()):
            count = storage.count
        roverFree = self.rover.cargo.capacity() - self.rover.cargo.count()
        if count > roverFree:
            count = roverFree
        storage.connect(self.rover.input)
        while count > 0:
            result = self.rover.input.take(itemId, count)
            if result.status in ("ok", "partial"):
                count -= result.moved
        self.rover.input.connect("")

    def loadAt(self, outpost, itemId, count=None, storageType=None):
        storage = storage_utils.getStorage(outpost, itemId, storageType)
        self.loadFromStorage(storage, itemId, count)

    def deliverToStorage(self, storage, itemId, count=None):
        self.moveTo(storage.x, storage.y)
        if (count is None) or (count > storage.free()):
            count = storage.free()
        if count > self.rover.cargo.count():
            count = self.rover.cargo.count()
        storage.connect(self.rover.output)
        while count > 0:
            result = self.rover.output.send(itemId, count)
            if result.status in ("ok", "partial"):
                count -= result.moved
        self.rover.output.connect("")

    def deliverTo(self, outpost, itemId, count=None, storageType=None):
        storage = storage_utils.getStorage(outpost, itemId, storageType)
        self.deliverToStorage(storage, itemId, count)

    def deliverAll(self, outpost, storageType=None):
        for item in self.rover.cargo.stacks():
            self.deliverTo(outpost, item.id, item.count, storageType)

    def freightLine(self, source, itemId, dest):
        fromStorage = storage_utils.getStorage(source, itemId)
        if type(dest) not in (type(()), type([])):
            dest = [dest]
        toStorages = [storage_utils.getStorage(outpost, itemId) for outpost in dest]
        toIdx = -1
        while True:
            roverFree = self.rover.cargo.capacity() - self.rover.cargo.count()
            while roverFree > 0:
                self.loadFromStorage(fromStorage, itemId, roverFree)
                roverFree = self.rover.cargo.capacity() - self.rover.cargo.count()
            if charge_utils.hasCharger(fromStorage.outpost):
                self.waitForCharge()
            while self.rover.cargo.count() > 0:
                options = [sto for sto in toStorages if sto.free() > 0]
                if not options:
                    sleep(rover_utils.SLEEP_INTERVAL)
                    continue
                toIdx = (toIdx + 1) % len(options)
                self.deliverToStorage(options[toIdx], itemId)
                if charge_utils.hasCharger(options[toIdx].outpost):
                    self.waitForCharge()
