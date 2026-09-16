SLEEP_INTERVAL = 0.1
BUY_RESERVE = 1000

collector = get_component("bio_collector_1")
exchange = get_component("bio_exchange_1")
planet = get_component("nocturna").id
journal = get_component("journal")
commander = get_component("commander")
shop = get_component("shop")
inventory = get_component("inventory")

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
            toBuy = needed - inventory.count(reagent)
            if toBuy > 0:
                waitForMoney()
                shop.buy(reagent, toBuy)
            self.input.take(reagent, needed)
    while self.extract().status == "output_full":
        sleep(SLEEP_INTERVAL)
    while self.output.send(fragId, 1).status != "ok":
        sleep(SLEEP_INTERVAL)

self.input.connect("inventory")
self.output.connect("inventory")
while True:
    processSample()