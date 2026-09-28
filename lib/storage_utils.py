SLEEP_INTERVAL = 0.1
STORAGE_TYPE_WAREHOUSE = "warehouse"
STORAGE_TYPE_LARGE_WAREHOUSE = "large_warehouse"
STORAGE_TYPE_LEAD_CASK = "lead_cask"
STORAGE_TYPE_BIN = "storage_bin"
STORAGE_TYPE_GAS_TANK = "gas_tank"
STORAGE_TYPE_LIQUID_TANK = "liquid_tank"
STORAGE_TYPE_LARGE_LIQUID_TANK = "bulk_liquid_reservoir"
STORAGE_TYPE_WAREHOUSES = (STORAGE_TYPE_LARGE_WAREHOUSE, STORAGE_TYPE_WAREHOUSE)
STORAGE_TYPE_SMALLEST_WAREHOUSES = tuple(reversed(STORAGE_TYPE_WAREHOUSES))
STORAGE_TYPE_LARGEST = (STORAGE_TYPE_LARGE_WAREHOUSE, STORAGE_TYPE_WAREHOUSE, STORAGE_TYPE_BIN)
STORAGE_TYPE_SMALLEST = tuple(reversed(STORAGE_TYPE_LARGEST))
STORAGE_TYPE_LIQUIDS = (STORAGE_TYPE_LARGE_LIQUID_TANK, STORAGE_TYPE_LIQUID_TANK)
STORAGE_TYPE_SMALLEST_LIQUIDS = tuple(reversed(STORAGE_TYPE_LIQUIDS))
ITEM_STORAGE_TYPE_MAP = {
    "ammonia": STORAGE_TYPE_GAS_TANK,
    "brine": STORAGE_TYPE_LIQUIDS,
    "chlorine": STORAGE_TYPE_GAS_TANK,
    "coastal_essence": STORAGE_TYPE_LIQUIDS,
    "cryofluid": STORAGE_TYPE_LIQUIDS,
    "deep_essence": STORAGE_TYPE_LIQUIDS,
    "fuel_rod": STORAGE_TYPE_LEAD_CASK,
    "frozen_essence": STORAGE_TYPE_LIQUIDS,
    "geothermal_essence": STORAGE_TYPE_LIQUIDS,
    "oil": STORAGE_TYPE_LIQUIDS,
    "quicksilver": STORAGE_TYPE_LIQUIDS,
    "raw_chlorine": STORAGE_TYPE_GAS_TANK,
    "raw_cryofluid": STORAGE_TYPE_LIQUIDS,
    "raw_quicksilver": STORAGE_TYPE_LIQUIDS,
    "raw_sulfur_gas": STORAGE_TYPE_GAS_TANK,
    "raw_uranium": STORAGE_TYPE_LEAD_CASK,
    "steam": STORAGE_TYPE_GAS_TANK,
    "sulfur_gas": STORAGE_TYPE_GAS_TANK,
    "swamp_gas": STORAGE_TYPE_GAS_TANK,
    "volcanic_essence": STORAGE_TYPE_LIQUIDS,
    "water": STORAGE_TYPE_LIQUIDS,
}


def getOutpost(outpost):
    if type(outpost) == type(""):
        outpostObj = get_component(outpost)
        if not outpostObj:
            outpostObj = get_component_by_name(outpost)
        return outpostObj
    if (type(outpost) in (type(()), type([]))) and (len(outpost) == 2):
        (x, y) = outpost
        nearest = None
        nearestD2 = None
        network = get_component("outpost_network")
        for outpostObj in network.outposts():
            dx = outpostObj.x - x
            dy = outpostObj.y - y
            dSquared = (dx * dx) + (dy * dy)
            if (nearest is None) or (dSquared < nearestD2):
                nearest = outpostObj
                nearestD2 = dSquared
        return nearest
    return outpost


class StorageHandler:
    """Generic base for other storages. Also works as handler for LeadCask"""
    def __init__(self, storage, itemId):
        self.storage = storage
        self.itemId = itemId

    @property
    def outpost(self):
        return self.storage.outpost

    @property
    def x(self):
        return self.outpost.x

    @property
    def y(self):
        return self.outpost.y

    def count(self):
        return self.storage.count(self.itemId)

    def capacity(self):
        return self.storage.capacity()

    def free(self):
        return self.capacity() - self.count()

    def connect(self, pipe):
        pipe.connect(self.storage.id)
        while pipe.connected_id() != self.storage.id:
            sleep(SLEEP_INTERVAL)


class StorageBinHandler(StorageHandler):
    """Handler for StorageBin"""
    def capacity(self):
        return self.storage.capacity()

    def free(self):
        return self.storage.space()


class WarehouseStorageHandler(StorageHandler):
    """Handler for WarehouseSlot"""
    def __init__(self, warehouse, slot, itemId):
        super().__init__(warehouse, itemId)
        self.slot = slot

    def count(self):
        return self.slot.count

    def capacity(self):
        return self.slot.capacity


class FluidStorageHandler(StorageHandler):
    """Handler for GasTank and (Large)LiquidTank"""
    def count(self):
        return self.storage.level()


def getStorage(outpost, itemId, storageType=None):
    outpost = getOutpost(outpost)
    if storageType is None:
        storageType = ITEM_STORAGE_TYPE_MAP.get(itemId, STORAGE_TYPE_LARGEST)
    if type(storageType) == type(""):
        storageType = [storageType]
    result = None
    for typeId in storageType:
        for building in outpost.buildings(typeId):
            building = get_component(building.id)
            if hasattr(building, "fluid"):
                if building.fluid() == itemId:
                    return FluidStorageHandler(building, itemId)
                if (not result) and (not building.fluid()):
                    result = FluidStorageHandler(building, itemId)
                continue
            if not hasattr(building, "count"):
                continue
            if building.count(itemId) > 0:
                if hasattr(building, "slots"):  # warehouse
                    for slot in building.slots():
                        if slot.item == itemId:
                            return WarehouseStorageHandler(building, slot, itemId)
                if hasattr(building, "get_capacity"): # bin
                    return StorageBinHandler(building, itemId)
                return StorageHandler(building, itemId)
            if result:
                continue
            if hasattr(building, "slots"):  # warehouse
                for slot in building.slots():
                    if slot.count <= 0:
                        result = WarehouseStorageHandler(building, slot, itemId)
                        break
            elif hasattr(building, "get_material"):  # bin
                if building.get_material() in (itemId, ""):
                    result = StorageBinHandler(building, itemId)
            elif building.material() in (itemId, ""):
                result = StorageHandler(building, itemId)
    return result


class InventoryStorageHandler(StorageHandler):
    """Handler for Inventory"""
    def __init__(self, itemId):
        super().__init__(get_component("inventory"), itemId)

    @property
    def outpost(self):
        return get_component("outpost_home")

    @property
    def x(self):
        return 0

    @property
    def y(self):
        return 0

    def capacity(self):
        return self.storage.get_size()

    def free(self):
        return self.storage.get_size() - self.storage.get_used()
