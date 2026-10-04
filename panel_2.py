import production_map
import storage_utils

fleet = get_component("fleet")


class Product:
    def __init__(self, itemId):
        self.itemId = itemId
        self.name = production_map.itemName(itemId)
        self.prefix = f"freight_{itemId}_"
        self.sourceName = None
        self.destNames = []
        for (outpostName, site) in production_map.PRODUCTION_SITES.items():
            if itemId in site.exports:
                self.sourceName = outpostName
                self.destNames = sorted(site.exports[itemId])
                break
        self.updateStorages()

    def updateStorages(self):
        self.sourceStorage = storage_utils.getStorage(self.sourceName, self.itemId)
        self.destStorages = []
        for destName in self.destNames:
            storage = storage_utils.getStorage(destName, self.itemId)
            self.destStorages.append(storage)

    def drawStatus(self, panel: Panel, x, y, maxX):
        overallStatus = "error"
        sourceCount = 0
        sourceCapacity = 0
        if self.sourceStorage:
            sourceCount = self.sourceStorage.count()
            sourceCapacity = self.sourceStorage.capacity()
        sourceProgress = 0
        sourceStatus = "error"
        if sourceCapacity > 0:
            overallStatus = "running"
            sourceProgress = sourceCount / sourceCapacity
            if sourceProgress >= 1:
                sourceStatus = "success"
            elif sourceProgress >= 0.5:
                sourceStatus = "warning"
            elif sourceCount <= 0:
                overallStatus = "idle"
        vehicles = [v for v in fleet.vehicles() if v.name.startswith(self.prefix)]
        destBars = []
        destsFull = True
        for storage in self.destStorages:
            if not storage:
                destBars.append({"progress": 1, "status": "error"})
                continue
            destProgress = storage.count() / storage.capacity()
            destStatus = "error"
            if destProgress >= 1:
                destStatus = "success"
            elif destProgress >= 0.5:
                destStatus = "warning"
            destBars.append({"progress": destProgress, "status": destStatus})
            if destProgress < 1:
                destsFull = False
        if len(destBars) <= 0:
            overallStatus = "error"
        elif (destsFull) and (overallStatus == "running"):
            overallStatus = "idle"
        panel.status_dot(x + 12, y + 12, 4, overallStatus)
        x += 24
        if sourceCapacity <= 0:
            panel.pill(x, y + 2, "Invalid", sourceStatus, size=21)
        else:
            panel.progress_bar(x, y, 72, 24, sourceProgress, sourceStatus)
        x += 82
        panel.draw_text(x, y + 12, f"{len(vehicles)}", size=16)
        x += 24
        panel.draw_text(x, y + 12, self.name, size=16)
        x = maxX - 60
        if len(destBars) <= 0:
            panel.pill(x, y, "None", "error", size=24)
        else:
            width = 60 / len(destBars)
            for bar in destBars:
                panel.vertical_bar(x, y, width - 2, 24, bar["progress"], bar["status"])
                x += width


products = []
for site in production_map.PRODUCTION_SITES.values():
    products.extend(Product(itemId) for itemId in site.exports.keys())
products.sort(key=lambda product: product.name)

while True:
    panel.clear()
    midpoint = panel.width() / 2
    panel.divider(midpoint, 0, midpoint, panel.height())
    panel.draw_text(24, 12, "Source", size=20)
    panel.draw_text(106, 12, "#", size=20)
    panel.draw_text(130, 12, "Product", size=20)
    panel.draw_text(midpoint - 60, 12, "Dest", size=20)
    panel.draw_text(midpoint + 24, 12, "Source", size=20)
    panel.draw_text(midpoint + 106, 12, "#", size=20)
    panel.draw_text(midpoint + 130, 12, "Product", size=20)
    panel.draw_text(panel.width() - 60, 12, "Dest", size=20)
    x = 0
    y = 22
    maxX = midpoint
    splitIdx = ceil(len(products) / 2)
    for i in range(len(products)):
        if i == splitIdx:
            x = midpoint
            y = 22
            maxX = panel.width()
        products[i].drawStatus(panel, x, y, maxX)
        y += 28
