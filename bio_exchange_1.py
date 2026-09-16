SLEEP_INTERVAL = 0.1

inventory = get_component("inventory")

def outstandingCount(order):
    return sum(order.requires.values()) - sum(order.delivered.values())

def deliverOrder():
    fillable = []
    actionable = []
    for order in self.orders():
        if order.status == "complete":
            continue
        isFillable = True
        isActionable = False
        for frag in order.requires.keys():
            needed = order.requires[frag] - order.delivered.get(frag, 0)
            if needed <= 0:
                continue
            have = inventory.count(frag)
            if have > 0:
                isActionable = True
            if have < needed:
                isFillable = False
            if isActionable and not isFillable:
                break
        if isFillable:
            fillable.append(order)
        elif isActionable:
            actionable.append(order)
    if fillable:
        fillable.sort(key=lambda order: -order.reward)
        order = fillable[0]
        self.set_order(order.id)
        for frag in order.requires.keys():
            needed = order.requires[frag] - order.delivered.get(frag, 0)
            if needed <= 0:
                continue
            self.input.take(frag, needed)
            while self.deliver().status == "ok":
                pass
        return
    if not actionable:
        sleep(SLEEP_INTERVAL)
        return
    actionable.sort(key=lambda order: (outstandingCount(order), -order.reward))
    order = actionable[0]
    self.set_order(order.id)
    for frag in order.requires.keys():
        needed = order.requires[frag] - order.delivered.get(frag, 0)
        if needed <= 0:
            continue
        have = inventory.count(frag)
        if have <= 0:
            continue
        self.input.take(frag, min(needed, have))
        while self.deliver().status == "ok":
            pass

self.input.connect("inventory")
while True:
    deliverOrder()