import cargo_rover_utils
import storage_utils

construction = get_component("construction_blueprint")

def getBlueprints():
    return construction.paused_constructions() + construction.pending_constructions()

class BuildRoverHandler(cargo_rover_utils.CargoRoverHandler):
    def loadBlueprintMaterials(self, blueprints):
        if type(blueprints) not in (type(()), type([])):
            blueprints = [blueprints]
        preloaded = {}
        for stack in self.rover.cargo.stacks():
            preloaded[stack.id] = preloaded.get(stack.id, 0) + stack.count
        for blueprint in blueprints:
            itemId = blueprint.required_item
            needed = blueprint.required_count
            if (not itemId) or (needed <= 0):
                continue
            if preloaded.get(itemId, 0) > 0:
                if preloaded[itemId] >= needed:
                    preloaded[itemId] -= needed
                    continue
                needed -= preloaded[itemId]
                preloaded[itemId] = 0
            storage = storage_utils.InventoryStorageHandler(itemId)
            self.loadFromStorage(storage, itemId, needed)

    def buildBlueprints(self, blueprints):
        self.loadBlueprintMaterials(blueprints)
        for blueprint in blueprints:
            self.moveTo(blueprint.position.x, blueprint.position.y)
            result = self.rover.constructor.execute(blueprint.id)
            while result.status != "ok":
                #TODO: handle error conditions
                result = self.rover.constructor.execute(blueprint.id)

    def buildBlueprint(self, blueprint):
        self.buildBlueprints([blueprint])
