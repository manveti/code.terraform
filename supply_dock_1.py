import storage_utils

clock = get_component("clock")
orders = get_component("orders")

def _isFillable(order):
    if (order.expires_day) and (clock.get_day() >= order.expires_day - 1):
        return False
    for (material, needed) in order.requires.items():
        storageName = storage_utils.formatStorage(material)
        storage = get_component_by_name(storageName)
        if (not storage) or (storage.count(material) < needed):
            return False
    return True

def _filterAndSort(lst):
    fillable = [order for order in lst if _isFillable(order)]
    fillable.sort(key=lambda ord: -ord.reward_credits / sum(ord.requires.values()))
    return fillable

def fillableWeeklyOrders():
    return _filterAndSort(orders.list_weekly_orders())

def fillableCampaignOrders():
    return _filterAndSort(orders.list_orders())

def fillOrder(order):
    self.set_order(order.id)
    self.set_enabled(True)
    for (material, needed) in order.requires.items():
        storageName = storage_utils.formatStorage(material)
        storage_utils.connectStorageName(self.input, storageName)
        notified = False
        while needed > 0:
            result = self.input.take(material, needed)
            if result.status in ("ok", "partial"):
                needed -= result.moved
                continue
            if not notified:
                notify(f"Couldn't take {material}: {result.message}", "warn", 0)
                notified = True
            sleep(storage_utils.SLEEP_INTERVAL)
    while sum(slot.count for slot in self.slots()) > 0:
        sleep(storage_utils.SLEEP_INTERVAL)

#print(fillableWeeklyOrders())
#print(fillableCampaignOrders())
fillOrder(fillableCampaignOrders()[1])