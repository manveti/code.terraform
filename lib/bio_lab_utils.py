import cargo_rover_utils
import storage_utils

BUY_RESERVE = 10000
SLEEP_INTERVAL = 0.1
WAREHOUSE_NAME = "warehouse_bio_lab"
REAGENT_COSTS = {
    "alkaline_buffer": 1,
    "cryo_solvent": 2,
    "protein_marker": 40,
    "chelating_agent": 200,
    "enzyme_solution": 1000,
}
REAGENT_STOCK_TARGET = 25
REAGENT_BUY_THRESHOLD = 10

planet = get_component("gps").planet().id
journal = get_component("journal")
commander = get_component("commander")
shop = get_component("shop")


class BioHandlerBase:
    def __init__(self, outpost):
        self.outpost = outpost
        self._collector = None
        self._lab = None
        self._exchange = None

    def getCollector(self):
        if not self._collector:
            buildings = self.outpost.buildings("bio_collector")
            if buildings:
                self._collector = get_component(buildings[0].id)
        return self._collector

    def getLab(self):
        if not self._lab:
            buildings = self.outpost.buildings("bio_lab")
            if buildings:
                self._lab = get_component(buildings[0].id)
        return self._lab

    def getExchange(self):
        if not self._exchange:
            buildings = self.outpost.buildings("bio_exchange")
            if buildings:
                self._exchange = get_component(buildings[0].id)
        return self._exchange

    def getOrderedFragments(self):
        ordered = set()
        exchange = self.getExchange()
        if not exchange:
            return ordered
        for order in exchange.orders():
            for (itemId, requested) in order.requires.items():
                delivered = order.delivered.get(itemId, 0) + order.in_transit.get(itemId, 0)
                if delivered < requested:
                    ordered.add(itemId)
        return ordered

    def getCatalogedFragments(self):
        return set(f.fragment_id for f in journal.cataloged_fragments(planet))

    def needFragment(self, itemId):
        if not itemId:
            return True
        if itemId not in self.getCatalogedFragments():
            return True
        return itemId in self.getOrderedFragments()


class BioCollectorHandler(BioHandlerBase):
    def __init__(self, collector):
        super().__init__(collector.outpost)
        self._collector = collector

    def waitForSpace(self):
        while self._collector.cargo:
            sleep(SLEEP_INTERVAL)

    def collectSamples(self):
        sites = [s for s in self._collector.scan() if self.needFragment(s.fragment_id)]
        if not sites:
            sleep(SLEEP_INTERVAL)
            return
        sites.sort(key=lambda site: site.distance)
        for site in sites:
            self.waitForSpace()
            self._collector.collect(site.coords)

    def collectLoop(self):
        while True:
            self.collectSamples()


def waitForMoney(self, itemId=None, count=0):
    targetMoney = BUY_RESERVE
    if (count > 0) and (itemId in REAGENT_COSTS):
        targetMoney += REAGENT_COSTS[itemId] * count
    while commander.get_credits() <= targetMoney:
        sleep(SLEEP_INTERVAL)


class BioLabHandler(BioHandlerBase):
    def __init__(self, lab):
        super().__init__(lab.outpost)
        self._lab = lab
        if lab.outpost.is_home:
            self.storage = get_component("inventory")
        else:
            self.storage = get_component_by_name(WAREHOUSE_NAME)
        self._lab.input.connect(self.storage.id)

    def waitForSample(self):
        collector = self.getCollector()
        while not collector:
            sleep(SLEEP_INTERVAL)
            collector = self.getCollector()
        while self._lab.take_from(collector).status != "ok":
            sleep(SLEEP_INTERVAL)

    def acquireReagents(self, toLoad):
        toAcquire = {}
        for (itemId, needed) in toLoad.items():
            onHand = self.storage.count(itemId)
            if onHand < needed:
                toAcquire[itemId] = needed - onHand
        if not toAcquire:
            return
        if self.outpost.is_home:
            for (itemId, toBuy) in toAcquire.items():
                waitForMoney(itemId, toBuy)
                shop.buy(itemId, toBuy)
            return
        baseMsg = f"Bio Lab at {self.outpost.name} needs reagents"
        msg = f"{baseMsg}: {toAcquire}"
        debug(msg)
        notify(baseMsg, level="warn", duration_seconds=0)
        waitNeeded = True
        while waitNeeded:
            waitNeeded = False
            sleep(SLEEP_INTERVAL)
            for (itemId, needed) in toLoad.items():
                onHand = self.storage.count(itemId)
                if onHand < needed:
                    waitNeeded = True
                    break

    def loadReagents(self, recipe):
        inInput = {}
        for stack in self._lab.input.stacks():
            if stack.id in recipe:
                inInput[stack.id] = inInput.get(stack.id, 0) + stack.count
        toLoad = {}
        for (itemId, demanded) in recipe.items():
            have = inInput.get(itemId, 0) + self._lab.loaded_reagents.get(itemId, 0)
            if demanded <= have:
                continue
            toLoad[itemId] = demanded - have
        self.acquireReagents(toLoad)
        for (itemId, needed) in toLoad.items():
            while needed > 0:
                result = self._lab.input.take(itemId, needed)
                if result.status in ("ok", "partial"):
                    needed -= result.moved
            needed = recipe[itemId] - self._lab.loaded_reagents.get(itemId, 0)
            self._lab.load(itemId, needed)

    def processSample(self):
        if not self._lab.specimen:
            self.waitForSample()
        result = self._lab.analyze()
        if result.status != "ok":
            return
        info = result.info
        itemId = self._lab.specimen.fragment_id
        if not self.needFragment(itemId):
            self._lab.discard()
            return
        self.loadReagents(info.required_recipe)
        while self._lab.extract().status != "ok":
            sleep(SLEEP_INTERVAL)

    def processLoop(self):
        while True:
            self.processSample()


class BioLabRoverHandler(cargo_rover_utils.CargoRoverHandler):
    def getReagentStorages(self, reagents):
        storages = {}
        freeSlots = []
        warehouse = get_component_by_name(WAREHOUSE_NAME)
        for slot in warehouse.slots():
            if not slot.item:
                freeSlots.append(slot)
                continue
            for itemId in reagents:
                if slot.item == itemId:
                    storages[itemId] = storage_utils.WarehouseStorageHandler(warehouse, slot, itemId)
                    break
        for itemId in reagents:
            if itemId not in storages:
                if not freeSlots:
                    return None
                storages[itemId] = storage_utils.WarehouseStorageHandler(warehouse, freeSlots.pop(0), itemId)
        return storages

    def stockBioLab(self, reagents):
        reagentInputs = {itemId: storage_utils.InventoryStorageHandler(itemId) for itemId in reagents}
        reagentStorages = self.getReagentStorages(reagents)
        while True:
            self.moveTo(0, 0)
            self.waitForCharge()
            needRun = False
            needed = {}
            for itemId in reagents:
                count = reagentStorages[itemId].count()
                if count < REAGENT_BUY_THRESHOLD:
                    needRun = True
                needed[itemId] = REAGENT_STOCK_TARGET - count
            if not needRun:
                sleep(SLEEP_INTERVAL)
                continue
            # load needed reagents
            for itemId in reagents:
                if itemId not in needed:
                    continue
                toLoad = needed[itemId] - self.cargoCount(itemId)
                if toLoad <= 0:
                    continue
                self.loadFromStorage(reagentInputs[itemId], itemId, toLoad)
                count = self.cargoCount(itemId)
                if count < needed[itemId]:
                    toBuy = needed[itemId] - count
                    waitForMoney(itemId, toBuy)
                    shop.buy(itemId, toBuy)
                    self.loadFromStorage(reagentInputs[itemId], itemId, toBuy)
            # deliver reagents
            for itemId in reagents:
                self.deliverToStorage(reagentStorages[itemId], itemId)
            self.waitForCharge()


class BioOrderHandler(BioHandlerBase):
    def __init__(self, outpost):
        super().__init__(outpost)
        if outpost.is_home:
            self.storage = get_component("inventory")
        else:
            self.storage = get_component_by_name(WAREHOUSE_NAME)

    def orderProperties(self, order):
        properties = None
        if order.target_glow:
            properties = {"glow": order.target_glow}
        #TODO: order.required_genes, possibly others
        return properties

    def ingredientGlowValid(self, stack, targetGlow):
        if not targetGlow:
            return True
        return stack.properties.get("glow") == targetGlow

    def stackMatchesOrder(self, stack, order):
        if stack.id not in order.requires:
            return False
        if not self.ingredientGlowValid(stack, order.target_glow):
            return False
        #TODO: order.required_genes, possibly others (use helpers to override in relevant subclasses)
        return True

    def ingredientCount(self, itemId, order):
        exchange = self.getExchange()
        count = 0
        for stack in self.storage.stacks() + exchange.input.stacks():
            if (stack.id != itemId) or (not self.stackMatchesOrder(stack, order)):
                continue
            count += stack.count
        return count

    def getOrders(self):
        exchange = self.getExchange()
        while not exchange:
            exchange = self.getExchange()
        fillable = []
        actionable = []
        for order in exchange.orders():
            if order.status == "complete":
                continue
            isFillable = True
            isActionable = False
            totNeeded = 0
            for (itemId, requested) in order.requires.items():
                delivered = order.delivered.get(itemId, 0) + order.in_transit.get(itemId, 0)
                needed = requested - delivered
                if needed <= 0:
                    continue
                totNeeded += needed
                have = self.ingredientCount(itemId, order)
                if have > 0:
                    isActionable = True
                if have < needed:
                    isFillable = False
            value = order.reward
            if totNeeded > 0:
                value /= totNeeded
            if isFillable:
                fillable.append((value, order))
            elif isActionable:
                actionable.append((value, order))
        sortKey = lambda entry: (-entry[0], -entry[1].reward)
        fillable.sort(key=sortKey)
        actionable.sort(key=sortKey)
        return [entry[1] for entry in fillable + actionable]


class BioExchangeHandler(BioOrderHandler):
    def __init__(self, exchange):
        super().__init__(exchange.outpost)
        self._exchange = exchange
        if exchange.outpost.is_home:
            self.upstream = self.getLab()
        else:
            self.upstream = None
            for buildingType in ("bio_luminizer",):
                buildings = self.outpost.buildings(buildingType)
                if buildings:
                    self.upstream = get_component(buildings[0].id)
        exchange.input.connect(self.upstream.id)

    def getOrder(self):
        orders = self.getOrders()
        if not orders:
            return None
        for order in orders:
            for stack in self._exchange.input.stacks():
                if self.stackMatchesOrder(stack, order):
                    return order
        return orders[0]

    def processOrder(self):
        for stack in self.upstream.output.stacks():
            self._exchange.input.take(stack.id, stack.count)
        order = self.getOrder()
        if not order:
            sleep(SLEEP_INTERVAL)
            return
        self._exchange.set_order(order.id)
        # clear out anything in our input that matches
        while self._exchange.deliver().status in ("ok", "output_full", "busy"):
            pass
        # update order after we're done with our input
        order = self._exchange.active_order()
        if not order:
            sleep(SLEEP_INTERVAL)
            return
        properties = self.orderProperties(order)
        for (itemId, requested) in order.requires.items():
            delivered = order.delivered.get(itemId, 0) + order.in_transit.get(itemId, 0)
            needed = requested - delivered
            if needed <= 0:
                continue
            have = self.ingredientCount(itemId, order)
            if have <= 0:
                continue
            toTake = min(needed, have)
            while toTake > 0:
                result = self._exchange.input.take(itemId, toTake, properties)
                if result.status in ("ok", "partial"):
                    toTake -= result.moved
                    while self._exchange.deliver().status in ("ok", "output_full", "busy"):
                        pass

    def processOrders(self):
        while True:
            self.processOrder()


class BioLuminizerHandler(BioOrderHandler):
    def __init__(self, luminizer):
        super().__init__(luminizer.outpost)
        self.luminizer = luminizer

    def waitForSample(self):
        if self.luminizer.chamber:
            return
        lab = self.getLab()
        while not lab:
            sleep(SLEEP_INTERVAL)
            lab = self.getLab()
        if self.luminizer.input.connected_id() != lab.id:
            self.luminizer.input.connect(lab.id)
            while self.luminizer.input.connected_id() != lab.id:
                sleep(SLEEP_INTERVAL)
        itemId = None
        while not itemId:
            for stack in self.luminizer.input.stacks():
                if stack.id in self.getCatalogedFragments():
                    itemId = stack.id
                    break
            if itemId:
                break
            for stack in lab.output.stacks():
                if stack.id in self.getCatalogedFragments():
                    itemId = stack.id
                    break
            if itemId:
                while self.luminizer.input.take(itemId, 1).status != "ok":
                    sleep(SLEEP_INTERVAL)
                break
            sleep(SLEEP_INTERVAL)
        while self.luminizer.load(itemId).status != "ok":
            sleep(SLEEP_INTERVAL)

    def ingredientGlowValid(self, stack, targetGlow):
        if not targetGlow:
            return True
        glowTuning = self.getGlowTuning(targetGlow, stack.properties.get("glow"))
        return bool(glowTuning)

    def ingredientCount(self, itemId, order):
        count = super().ingredientCount(itemId, order)
        if (self.luminizer.chamber) and (self.luminizer.chamber.fragment_id == itemId):
            count += 1
        return count

    def getTargetGlow(self, itemId):
        for order in self.getOrders():
            ordered = order.requires.get(itemId, 0)
            if ordered <= 0:
                continue
            delivered = order.delivered.get(itemId, 0) + order.in_transit.get(itemId, 0)
            if delivered >= ordered:
                continue
            return order.target_glow
        return False

    def getGlowTuning(self, targetGlow, curGlow):
        if (not targetGlow) or (not curGlow) or (len(targetGlow) != len(curGlow)):
            return None
        r = self.luminizer.lamp_signature("red")
        g = self.luminizer.lamp_signature("green")
        b = self.luminizer.lamp_signature("blue")
        tgt = [targetGlow[i] - curGlow[i] for i in range(len(targetGlow))]
        # let's try to remember mid school algebra to solve three equations for three unknowns...
        # r[0]*x + g[0]*y + b[0]*z = tgt[0]
        # r[1]*x + g[1]*y + b[1]*z = tgt[1]
        # r[2]*x + g[2]*y + b[2]*z = tgt[2]
        
        # solve for x in 1st equation:
        # x = (tgt[0] - g[0]*y - b[0]*z) / r[0]
        
        # substitute into other two equations:
        # (r[0]*g[1] - r[1]*g[0])*y + (r[0]*b[1] - r[1]*b[0])*z = r[0]*tgt[1] - r[1]*tgt[0]
        # (r[0]*g[2] - r[1]*g[0])*y + (r[0]*b[2] - r[1]*b[0])*z = r[0]*tgt[2] - r[2]*tgt[0]
        
        # solve for y in 2nd equation:
        # y = ((r[0]*tgt[1] - r[1]*tgt[0]) - (r[0]*b[1] - r[1]*b[0])*z) / (r[0]*g[1] - r[1]*g[0])
        
        # substitute into final equation:
        # (r[0]*g[2] - r[1]*g[0])
        # * (((r[0]*tgt[1] - r[1]*tgt[0]) - (r[0]*b[1] - r[1]*b[0]) * z) / (r[0]*g[1] - r[1]*g[0]))
        # + (r[0]*b[2] - r[1]*b[0]) * z
        # = r[0]*tgt[2] - r[2]*tgt[0]
    
        # simplify:
        # z = (
        #         (r[0]*g[1] - r[1]*g[0]) * (r[0]*tgt[2] - r[2]*tgt[0])
        #       - (r[0]*g[2] - r[1]*g[0]) * (r[0]*tgt[1] - r[1]*tgt[0])
        #     )
        #   / (
        #         (r[0]*g[1] - r[1]*g[0]) * (r[0]*b[2] - r[1]*b[0])
        #       - (r[0]*g[2] - r[1]*g[0]) * (r[0]*b[1] - r[1]*b[0])
        #     )
        num = (r[0] * g[1] - r[1] * g[0]) * (r[0] * tgt[2] - r[2] * tgt[0])
        num -= (r[0] * g[2] - r[1] * g[0]) * (r[0] * tgt[1] - r[1] * tgt[0])
        denom = (r[0] * g[1] - r[1] * g[0]) * (r[0] * b[2] - r[1] * b[0])
        denom -= (r[0] * g[2] - r[1] * g[0]) * (r[0] * b[1] - r[1] * b[0])
        if denom == 0:
            return None
        z = num / denom
        y = ((r[0]*tgt[1] - r[1]*tgt[0]) - (r[0]*b[1] - r[1]*b[0])*z) / (r[0]*g[1] - r[1]*g[0])
        x = (tgt[0] - g[0]*y - b[0]*z) / r[0]
        # validate solution
        for i in range(len(targetGlow)):
            if curGlow[i] + (x * r[i]) + (y * g[i]) + (z * b[i]) != targetGlow[i]:
                return None
        return (x, y, z)

    def processSample(self):
        self.waitForSample()
        itemId = self.luminizer.chamber.fragment_id
        targetGlow = self.getTargetGlow(itemId)
        if targetGlow is False:
            sleep(SLEEP_INTERVAL)
            return
        curGlow = self.luminizer.chamber.glow
        if (not targetGlow) or (targetGlow == curGlow):
            self.luminizer.discard()
            return
        tuning = self.getGlowTuning(targetGlow, curGlow)
        if not tuning:
            sleep(SLEEP_INTERVAL)
            return
        while self.luminizer.set_lamps(*tuning).status != "ok":
            sleep(SLEEP_INTERVAL)
        while self.luminizer.infuse().status != "ok":
            sleep(SLEEP_INTERVAL)

    def processLoop(self):
        while True:
            self.processSample()
