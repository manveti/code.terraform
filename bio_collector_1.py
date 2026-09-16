SLEEP_INTERVAL = 0.1

exchange = get_component("bio_exchange_1")
planet = get_component("nocturna").id
journal = get_component("journal")

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

def waitForSpace():
    while self.cargo:
        sleep(SLEEP_INTERVAL)

def collectSamples():
    sites = [s for s in self.scan() if needFragment(s.fragment_id)]
    if not sites:
        sleep(SLEEP_INTERVAL)
        return
    sites.sort(key=lambda site: site.distance)
    for site in sites:
        waitForSpace()
        self.collect(site.coords)

while True:
    collectSamples()