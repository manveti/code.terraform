import production_map
import storage_utils

DEFAULT_BATCH_SIZE = 10
CHANNEL = "production_requests"


class ProductionRequester:
    def __init__(self):
        self._comms = None

    def getComms(self):
        if not self._comms:
            self._comms = get_component("comms")
        return self._comms

    def requestProduction(self, itemId, count):
        comms = self.getComms()
        while not comms:
            sleep(storage_utils.SLEEP_INTERVAL)
            comms = self.getComms()
        msg = {"item": itemId, "count": count}
        result = comms.send(CHANNEL, msg)
        while result.status != "ok":
            sleep(storage_utils.SLEEP_INTERVAL)
            result = comms.send(CHANNEL, msg)

    def cancelProduction(self, itemId):
        comms = self.getComms()
        while not comms:
            sleep(storage_utils.SLEEP_INTERVAL)
            comms = self.getComms()
        toCancel = []
        for msg in comms.pending(CHANNEL):
            if msg.value.get("item") == itemId:
                toCancel.append(msg.id)
        for msgId in toCancel:
            comms.cancel(CHANNEL, msgId)


class ProducerHandler:
    def __init__(self, machine):
        self._comms = None
        self._storage = {}
        self.machine = machine
        self.outpost = storage_utils.getOutpost(machine.outpost)
        self.produces = set()
        self._exports = {}
        self.onDemand = set()
        productionSite = production_map.PRODUCTION_SITES.get(machine.outpost.name)
        if productionSite:
            self.produces = productionSite.produces
            self._exports = productionSite.exports
            self.onDemand = productionSite.onDemand

    def getComms(self):
        if not self._comms:
            self._comms = get_component("comms")
        return self._comms

    def getStorage(self, outpostName, itemId):
        if outpostName not in self._storage:
            self._storage[outpostName] = {}
        if (itemId not in self._storage[outpostName]) or (not self._storage[outpostName][itemId].valid()):
            storage = storage_utils.getStorage(outpostName, itemId)
            if not storage:
                return storage
            self._storage[outpostName][itemId] = storage
        return self._storage[outpostName][itemId]

    def getExports(self, itemId):
        return self._exports.get(itemId, set())

    def portToItemId(self, port):
        """Translate port name (e.g. "water_in") to material ID (e.g. "water")"""
        return port.rsplit("_", 1)[0]

    def recipeIngredientsAvailable(self, recipe):
        """How many instances of the given recipe we have ingredients to produce"""
        minAvail = None
        for (itemId, count) in recipe.inputs.items():
            storage = self.getStorage(self.outpost.name, itemId)
            if not storage:
                return 0
            avail = floor(storage.count() / count)
            if avail <= 0:
                return 0
            if (minAvail is None) or (avail < minAvail):
                minAvail = avail
        for (port, count) in recipe.fluid_inputs.items():
            itemId = recipe.input_fluid
            if not itemId:
                itemId = self.portToItemId(port)
            storage = self.getStorage(self.outpost.name, itemId)
            if not storage:
                return 0
            avail = floor(storage.count() / count)
            if avail <= 0:
                return 0
            if (minAvail is None) or (avail < minAvail):
                minAvail = avail
        return minAvail or 0

    def recipeSpaceAvailable(self, recipe):
        """How many instances of the given recipe we have space to store locally"""
        minSpace = None
        if (recipe.output_item) and (recipe.output_count > 0):
            storage = self.getStorage(self.outpost.name, recipe.output_item)
            if not storage:
                return 0
            minSpace = floor(storage.free() / recipe.output_count)
            if minSpace <= 0:
                return 0
        if (recipe.byproduct_item) and (recipe.byproduct_count > 0):
            storage = self.getStorage(self.outpost.name, recipe.byproduct_item)
            if not storage:
                return 0
            space = floor(storage.free() / recipe.byproduct_count)
            if space <= 0:
                return 0
            if (minSpace is None) or (space < minSpace):
                minSpace = space
        if recipe.fluid_outputs:
            for (portName, count) in recipe.fluid_outputs.items():
                itemId = self.portToItemId(portName)
                storage = self.getStorage(self.outpost.name, itemId)
                if not storage:
                    return 0
                space = floor(storage.free() / count)
                if space <= 0:
                    return 0
                if (minSpace is None) or (space < minSpace):
                    minSpace = space
        return minSpace or 0

    def recipeDemand(self, recipe):
        """Free space ratio for the given recipe.
        I.e. how many instances could be stored globally right now divided by
        how many instances could be stored globally if all storage were empty"""
        minRatio = None
        if (recipe.output_item) and (recipe.output_count > 0):
            storage = self.getStorage(self.outpost.name, recipe.output_item)
            if not storage:
                return 0
            free = storage.free()
            capacity = storage.capacity()
            for outpost in self.getExports(recipe.output_item):
                storage = self.getStorage(outpost, recipe.output_item)
                if not storage:
                    continue
                free += storage.free()
                capacity += storage.capacity()
            free = floor(free / recipe.output_count)
            minRatio = free / capacity
            if minRatio <= 0:
                return 0
        if (recipe.byproduct_item) and (recipe.byproduct_count > 0):
            storage = self.getStorage(self.outpost.name, recipe.byproduct_item)
            if not storage:
                return 0
            free = storage.free()
            capacity = storage.capacity()
            for outpost in self.getExports(recipe.byproduct_item):
                storage = self.getStorage(outpost, recipe.byproduct_item)
                if not storage:
                    continue
                free += storage.free()
                capacity += storage.capacity()
            free = floor(free / recipe.byproduct_count)
            ratio = free / capacity
            if ratio <= 0:
                return 0
            if (minRatio is None) or (ratio < minRatio):
                minRatio = ratio
        if recipe.fluid_outputs:
            for (portName, count) in recipe.fluid_outputs.items():
                itemId = self.portToItemId(portName)
                storage = self.getStorage(self.outpost.name, itemId)
                if not storage:
                    return 0
                free = storage.free()
                capacity = storage.capacity()
                for outpost in self.getExports(itemId):
                    storage = self.getStorage(outpost, itemId)
                    if not storage:
                        continue
                    free += storage.free()
                    capacity += storage.capacity()
                free = floor(free / count)
                ratio = free / capacity
                if ratio <= 0:
                    return 0
                if (minRatio is None) or (ratio < minRatio):
                    minRatio = ratio
        return minRatio or 0

    def recipeInputSize(self, recipe):
        """How much space the given recipe takes up in the machine's input"""
        return sum(needed for needed in recipe.inputs.values())

    def producesRecipe(self, recipe):
        if not self.produces:
            return True
        if (recipe.output_item) and (recipe.output_item in self.produces):
            return True
        if recipe.fluid_outputs:
            for portName in recipe.fluid_outputs.keys():
                itemId = self.portToItemId(portName)
                if itemId in self.produces:
                    return True
        return False

    def getRecipes(self, filtered=True):
        pred = lambda recipe: recipe
        if filtered:
            pred = lambda recipe: self.producesRecipe(recipe)
        return [recipe for recipe in self.machine.list_recipes() if pred(recipe)]

    def connectOutputs(self, recipe):
        storage = self.getStorage(self.outpost.name, recipe.output_item)
        while not storage:
            sleep(storage_utils.SLEEP_INTERVAL)
            storage = self.getStorage(self.outpost.name, recipe.output_item)
        storage.connect(self.machine.output)
        if recipe.byproduct_item:
            storage = self.getStorage(self.outpost.name, recipe.byproduct_item)
            while not storage:
                sleep(storage_utils.SLEEP_INTERVAL)
                storage = self.getStorage(self.outpost.name, recipe.byproduct_item)
            storage.connect(self.machine.byproduct)
        if not recipe.fluid_outputs:
            return
        for portName in recipe.fluid_outputs.keys():
            itemId = self.portToItemId(portName)
            storage = self.getStorage(self.outpost.name, itemId)
            while not storage:
                sleep(storage_utils.SLEEP_INTERVAL)
                storage = self.getStorage(self.outpost.name, itemId)
            storage.connect(getattr(self.machine, portName))

    def connectInputs(self, recipe):
        if not recipe.fluid_inputs:
            return
        for portName in recipe.fluid_inputs.keys():
            itemId = self.portToItemId(portName)
            storage = self.getStorage(self.outpost.name, itemId)
            while not storage:
                sleep(storage_utils.SLEEP_INTERVAL)
                storage = self.getStorage(self.outpost.name, itemId)
            storage.connect(getattr(self.machine, portName))

    def takeRecipe(self, recipe, count):
        available = self.recipeIngredientsAvailable(recipe)
        if available < count:
            count = available
        if count <= 0:
            return 0
        storage = {}
        for itemId in recipe.inputs.keys():
            storage[itemId] = self.getStorage(self.outpost.name, itemId)
            if not storage[itemId]:
                return 0
        for (itemId, needed) in recipe.inputs.items():
            needed *= count
            storage[itemId].connect(self.machine.input)
            while needed > 0:
                result = self.machine.input.take(itemId, needed)
                if result.status in ("ok", "partial"):
                    needed -= result.moved
                else:
                    sleep(storage_utils.SLEEP_INTERVAL)
        self.machine.input.connect("")
        return count

    def setupProductionRun(self, recipe):
        result = self.machine.set_recipe(recipe.id)
        while result.status != "ok":
            if result.status not in ("busy", "output_busy"):
                print(f"Couldn't set recipe {recipe.id}: {result.message}")
            sleep(storage_utils.SLEEP_INTERVAL)
            result = self.machine.set_recipe(recipe.id)
        self.connectOutputs(recipe)
        self.connectInputs(recipe)

    def flowOutput(self, recipe):
        outputMoved = False
        if hasattr(self.machine, "output"):
            count = self.machine.output.count()
            if count > 0:
                result = self.machine.output.send(recipe.output_item, count)
                if result.status in ("ok", "partial"):
                    outputMoved = result.moved
                else:
                    outputMoved = True
        if recipe.byproduct_item:
            count = self.machine.byproduct.count()
            if count > 0:
                self.machine.byproduct.send(recipe.byproduct_item, count)
                if not outputMoved:
                    outputMoved = True
        return outputMoved

    def disconnectInput(self, recipe):
        if recipe.fluid_inputs:
            for portName in recipe.fluid_inputs.keys():
                getattr(self.machine, portName).disconnect()

    def disconnectOutput(self, recipe):
        if hasattr(self.machine, "output"):
            while self.machine.output.count() > 0:
                result = self.machine.output.send(recipe.output_item, self.machine.output.count())
                if result.status not in ("ok", "partial"):
                    sleep(storage_utils.SLEEP_INTERVAL)
            self.machine.output.connect("")
        if recipe.byproduct_item:
            while self.machine.byproduct.count() > 0:
                result = self.machine.byproduct.send(recipe.byproduct_item, self.machine.byproduct.count())
                if result.status not in ("ok", "partial"):
                    sleep(storage_utils.SLEEP_INTERVAL)
            self.machine.byproduct.connect("")
        if recipe.fluid_outputs:
            for portName in recipe.fluid_outputs.keys():
                port = getattr(self.machine, portName)
                while port.level() > 0:
                    if port.flow_rate() <= 0:
                        sleep(storage_utils.SLEEP_INTERVAL)
                getattr(self.machine, portName).disconnect()

    def monitorProductionRun(self, recipe, count):
        size = self.recipeInputSize(recipe)
        while count > 0:
            outputMoved = self.flowOutput(recipe)
            idle = not outputMoved
            if recipe.inputs:
                inputSpace = self.machine.input.capacity() - self.machine.input.count()
                takeCount = min(floor(inputSpace / size), count)
                if takeCount > 0:
                    count -= self.takeRecipe(recipe, takeCount)
                    idle = False
            else:
                count -= outputMoved
                if self.machine.output.count() >= count:
                    break
            if idle:
                sleep(storage_utils.SLEEP_INTERVAL)

    def finishProductionRun(self, recipe):
        self.disconnectInput(recipe)
        while self.machine.is_running():
            if not self.flowOutput(recipe):
                sleep(storage_utils.SLEEP_INTERVAL)
        self.machine.clear_recipe()
        self.disconnectOutput(recipe)

    def productionRun(self, recipe, count=DEFAULT_BATCH_SIZE):
        self.setupProductionRun(recipe)
        self.monitorProductionRun(recipe, count)
        self.finishProductionRun(recipe)

    def getProductionRequest(self):
        comms = self.getComms()
        if not comms:
            return None
        recipes = {}
        for recipe in self.machine.list_recipes():
            if recipe.output_item in self.onDemand:
                recipes[recipe.output_item] = recipe
        for msg in comms.pending(CHANNEL):
            itemId = msg.value.get("item")
            recipe = recipes.get(itemId)
            if not recipe:
                continue
            reqCount = msg.value.get("count", 0)
            if reqCount <= 0:
                continue
            count = reqCount
            avail = self.recipeIngredientsAvailable(recipe)
            if avail < count:
                count = avail
            if count <= 0:
                continue
            space = self.recipeSpaceAvailable(recipe)
            if space < count:
                count = space
            if count <= 0:
                continue
            if count < reqCount:
                newMsg = msg.value.copy()
                newMsg["count"] = reqCount - count
                result = comms.update(CHANNEL, msg.id, newMsg)
                if result.status != "ok":
                    continue
            else:
                result = comms.receive(CHANNEL, msg.id)
                if result.status != "ok":
                    continue
            return (msg.value["item"], count)

    def productionLoop(self, batch=DEFAULT_BATCH_SIZE):
        lastRecipe = None
        while True:
            recipe = None
            count = 0
            request = self.getProductionRequest()
            if request:
                (recipe, count) = request
            if (not recipe) or (count <= 0):
                recipes = self.getRecipes()
                recipes.sort(key=lambda recipe: -self.recipeDemand(recipe))
                while (recipes) and (count <= 0):
                    recipe = recipes.pop(0)
                    count = batch
                    avail = self.recipeIngredientsAvailable(recipe)
                    if avail < count:
                        count = avail
                    space = self.recipeSpaceAvailable(recipe)
                    if space < count:
                        count = space
            if (not recipe) or (count <= 0):
                if lastRecipe:
                    self.finishProductionRun(lastRecipe)
                    lastRecipe = None
                sleep(storage_utils.SLEEP_INTERVAL)
                continue
            if (lastRecipe) and (recipe.id != lastRecipe.id):
                self.finishProductionRun(lastRecipe)
            if (not lastRecipe) or (recipe.id != lastRecipe.id):
                self.setupProductionRun(recipe)
            lastRecipe = recipe
            self.monitorProductionRun(recipe, count)
