SLEEP_INTERVAL = 0.1
HEAT_BUFFER = 10
MIN_ROW = ord("A")
MAX_ROW = ord("H")
MIN_COL = 1
MAX_COL = 24

scanner = get_component("scanner_1")
inventory = get_component("inventory")
shop = get_component("shop")

def formatPos(row, col):
    return f"{chr(row)}{col}"

def findItem(row, col):
    scan = scanner.get_scanned()
    checked = set()
    toCheck = [(row, col)]
    while toCheck:
        (row, col) = toCheck.pop(0)
        pos = formatPos(row, col)
        if scan[pos].status == "ok":
            return (row, col)
        for next in [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]:
            if next in checked:
                continue
            if (next[0] < MIN_ROW) or (next[0] > MAX_ROW):
                continue
            if (next[1] < MIN_COL) or (next[1] > MAX_COL):
                continue
            toCheck.append(next)
            checked.add(next)

def waitForHeat():
    while self.get_heat() >= self.get_max_heat() - HEAT_BUFFER:
        sleep(SLEEP_INTERVAL)

def moveStep(row, col):
    waitForHeat()
    while self.move(formatPos(row, col)).status != "ok":
        sleep(SLEEP_INTERVAL)

def moveToPos(row, col, dest):
    while row < dest[0]:
        row += 1
        moveStep(row, col)
    while row > dest[0]:
        row -= 1
        moveStep(row, col)
    while col < dest[1]:
        col += 1
        moveStep(row, col)
    while col > dest[1]:
        col -= 1
        moveStep(row, col)

def collectItem(row, col):
    while True:
        waitForHeat()
        result = self.collect()
        if result.status in ("ok", "empty"):
            return result.id
        if result.status == "holding":
            storeItem()
        else:
            sleep(SLEEP_INTERVAL)

def storeItem():
    while self.store().status == "inventory_full":
        while not inventory.has_space():
            sleep(SLEEP_INTERVAL)

def harvestItem():
    pos = self.get_position()
    row = ord(pos[0])
    col = int(pos[1:])
    itemPos = findItem(row, col)
    if not itemPos:
        sleep(SLEEP_INTERVAL)
        return
    moveToPos(row, col, itemPos)
    collectedId = collectItem(row, col)
    if collectedId:
        storeItem()
        shop.sell(collectedId)

while True:
    harvestItem()