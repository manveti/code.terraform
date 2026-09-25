import rover_utils
import storage_utils


class CargoRoverHandler(rover_utils.RoverHandler):
    #TODO: make "thread-safe"; bins and the like are fine, but warehouses have one i/o port for multiple slots
    def loadAt(self, outpost, itemId, count=None, storageType=None):
        storage = storage_utils.getStorage(outpost, itemId, storageType)
        if (count is None) or (count > storage.count):
            count = storage.count
        roverFree = self.rover.cargo.capacity() - self.rover.cargo.full()
        if count > roverFree:
            count = roverFree
        self.moveTo(outpost.x, outpost.y)
        storage.connect(self.rover.input)
        while count > 0:
            result = self.rover.input.take(itemId, count)
            if result.status in ("ok", "partial"):
                count -= result.moved
        self.rover.input.connect("")

    def deliverTo(self, outpost, itemId, count=None, storageType=None):
        storage = storage_utils.getStorage(outpost, itemId, storageType)
        if (count is None) or (count > storage.free()):
            count = storage.free()
        if count > self.rover.cargo.count():
            count = self.rover.cargo.count()
        self.moveTo(outpost.x, outpost.y)
        storage.connect(self.rover.output)
        while count > 0:
            result = self.rover.output.send(itemId, count)
            if result.status in ("ok", "partial"):
                count -= result.moved
        self.rover.output.connect("")

    def deliverAll(self, outpost, storageType=None):
        for item in self.rover.cargo.stacks():
            self.deliverTo(outpost, item.id, item.count, storageType)
