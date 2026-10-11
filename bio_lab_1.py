SLEEP_INTERVAL = 0.1
BUY_RESERVE = 10000

collector = get_component(self.outpost.buildings("bio_collector")[0].id)
exchange = get_component(self.outpost.buildings("bio_exchange")[0].id)
planet = get_component("nocturna").id
journal = get_component("journal")
commander = get_component("commander")
shop = get_component("shop")
inventoryIn = get_component("inventory")
inventoryOut = get_component("inventory")
if not self.outpost.is_home:
    inventoryIn = get_component_by_name("warehouse_bio_reagents")
    inventoryOut = get_component_by_name("storage_bin_bio_samples")

def getOrderedFragments():
    ordered = set()
    for order in exchange.orders():
        for frag in order.requires.keys():
            if order.delivered.get(frag, 0) < order.requires[frag]:
                ordered.add(frag)
    return ordered

def getCatalogedFragments():
    return set(f.fragment_id for f in journal.cataloged_fragments(planet))

def needFragment(fragId):
    if fragId is None:
        return True
    if fragId not in getCatalogedFragments():
        return True
    return fragId in getOrderedFragments()

def waitForSample():
    while self.take_from(collector).status != "ok":
        sleep(SLEEP_INTERVAL)

def waitForMoney():
    while commander.get_credits() <= BUY_RESERVE:
        sleep(SLEEP_INTERVAL)

def processSample():
    if not self.specimen:
        waitForSample()
    result = self.analyze()
    if result.status != "ok":
        return
    info = result.info
    fragId = self.specimen.fragment_id
    if not needFragment(fragId):
        self.discard()
        return
    for reagent in info.required_recipe.keys():
        loaded = self.loaded_reagents.get(reagent, 0)
        needed = info.required_recipe[reagent] - loaded
        while needed > 0:
            if self.load(reagent, needed).status == "ok":
                break
            loaded = self.loaded_reagents.get(reagent, 0)
            needed = info.required_recipe[reagent] - loaded
            toBuy = needed - inventoryIn.count(reagent)
            if toBuy > 0:
                waitForMoney()
                shop.buy(reagent, toBuy)
            #TODO: if not self.outpost.is_home: request and wait for delivery
            self.input.take(reagent, needed)
    while self.extract().status == "output_full":
        sleep(SLEEP_INTERVAL)
    while self.output.send(fragId, 1).status != "ok":
        sleep(SLEEP_INTERVAL)

self.input.connect(inventoryIn.id)
self.output.connect(inventoryOut.id)
while True:
    processSample()
