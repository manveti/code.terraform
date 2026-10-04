import production_map
import production_utils
import storage_utils

OVERVIEW = "Overview"
INPUT_STATUS_INVALID = 0
INPUT_STATUS_EMPTY = 1
INPUT_STATUS_VALID = 2
INPUT_STATUS_FULL = 3


class ProductionInput:
    def __init__(self, itemId, fed, storage):
        self.name = production_map.itemName(itemId)
        self.fed = fed
        self.storage = storage

    def full(self):
        if not self.storage:
            return False
        return self.storage.free() <= 0

    def empty(self):
        if not self.storage:
            return True
        return self.storage.count() <= 0

    def status(self):
        if (not self.storage) or (not self.fed):
            return INPUT_STATUS_INVALID
        if self.empty():
            return INPUT_STATUS_EMPTY
        if self.full():
            return INPUT_STATUS_FULL
        return INPUT_STATUS_VALID


class ProductionOutput:
    def __init__(self, itemId, inputs, localStorage, exportStorage):
        self.name = production_map.itemName(itemId)
        self.inputs = sorted(inputs, key=lambda itm: production_map.itemName(itm))
        self.localStorage = localStorage
        self.exportStorage = [storage for storage in exportStorage if storage]

    def inputStatus(self, inputs):
        if not self.inputs:
            return INPUT_STATUS_INVALID
        minStatus = INPUT_STATUS_FULL
        for itemId in self.inputs:
            if itemId not in inputs:
                return INPUT_STATUS_INVALID
            status = inputs[itemId].status()
            if status < minStatus:
                minStatus = status
        return minStatus

    def localCount(self):
        if not self.localStorage:
            return 0
        return self.localStorage.count()

    def localCapacity(self):
        if not self.localStorage:
            return 0
        return self.localStorage.capacity()

    def fullCount(self):
        count = self.localCount()
        for storage in self.exportStorage:
            count += storage.count()
        return count

    def fullCapacity(self):
        capacity = self.localCapacity()
        for storage in self.exportStorage:
            capacity += storage.capacity()
        return capacity


class ProductionOutpost:
    def __init__(self, siteName):
        self.name = siteName
        self.site = production_map.PRODUCTION_SITES[siteName]
        self.outpost = storage_utils.getOutpost(siteName)
        self.updateLinks()

    def updateLinks(self):
        if not self.outpost:
            self.valid = False
            self.inputs = {}
            self.outputs = [
                ProductionOutput(itemId, {}, None, [])
                for itemId in production_map.PRODUCTION_SITES[self.name].produces
            ]
            return
        inputs = {}
        outputs = {}
        for building in self.outpost.buildings():
            building = get_component(building.id)
            if not hasattr(building, "list_recipes"):
                continue
            producer = production_utils.ProducerHandler(building)
            for recipe in producer.getRecipes():
                recipeInputs = set()
                for itemId in recipe.inputs.keys():
                    recipeInputs.add(itemId)
                    if itemId in inputs:
                        continue
                    fed = (itemId in self.site.local) or (itemId in self.site.produces)
                    for site in production_map.PRODUCTION_SITES.values():
                        if itemId not in site.exports:
                            continue
                        if self.name in site.exports[itemId]:
                            fed = True
                    storage = producer.getStorage(self.name, itemId)
                    inputs[itemId] = ProductionInput(itemId, fed, storage)
                for port in recipe.fluid_inputs.keys():
                    itemId = production_utils.portToItemId(port)
                    recipeInputs.add(itemId)
                    if itemId in inputs:
                        continue
                    fed = (itemId in self.site.local) or (itemId in self.site.produces)
                    for site in production_map.PRODUCTION_SITES.values():
                        if itemId not in site.exports:
                            continue
                        if self.name in site.exports[itemId]:
                            fed = True
                    storage = producer.getStorage(self.name, itemId)
                    inputs[itemId] = ProductionInput(itemId, fed, storage)
                for itemId in (recipe.output_item, recipe.byproduct_item):
                    if (not itemId) or (itemId in outputs):
                        continue
                    localStorage = producer.getStorage(self.name, itemId)
                    exportStorage = [
                        producer.getStorage(site, itemId)
                        for site in producer.getExports(itemId)
                    ]
                    outputs[itemId] = ProductionOutput(
                        itemId, recipeInputs, localStorage, exportStorage
                    )
                if not recipe.fluid_outputs:
                    continue
                for port in recipe.fluid_outputs.keys():
                    itemId = production_utils.portToItemId(port)
                    if itemId in outputs:
                        continue
                    localStorage = producer.getStorage(self.name, itemId)
                    exportStorage = [
                        producer.getStorage(site.name, itemId)
                        for site in producer.getExports(itemId)
                    ]
                    outputs[itemId] = ProductionOutput(
                        itemId, recipeInputs, localStorage, exportStorage
                    )
        self.valid = True
        self.inputs = {}
        self.outputs = []
        for itemId in self.site.produces:
            if itemId not in outputs:
                self.valid = False
                self.outputs.append(ProductionOutput(itemId, [], None, []))
                continue
            self.outputs.append(outputs[itemId])
            for inputId in outputs[itemId].inputs:
                if inputId not in inputs:
                    self.valid = False
                    continue
                if inputId not in self.inputs:
                    self.inputs[inputId] = inputs[inputId]
        self.outputs.sort(key=lambda output: output.name)

    def drawSummary(self, pane: Panel, x, y):
        totalInputs = len(self.outputs)
        validInputs = 0
        nonemptyInputs = 0
        fullInputs = 0
        localCount = 0
        localCapacity = 0
        fullCount = 0
        fullCapacity = 0
        for output in self.outputs:
            status = output.inputStatus(self.inputs)
            if status <= INPUT_STATUS_INVALID:
                continue
            validInputs += 1
            if status <= INPUT_STATUS_EMPTY:
                continue
            nonemptyInputs += 1
            if status >= INPUT_STATUS_FULL:
                fullInputs += 1
            localCount += output.localCount()
            localCapacity += output.localCapacity()
            fullCount += output.fullCount()
            fullCapacity += output.fullCapacity()
        overallStatus = "error"
        if self.valid:
            overallStatus = "running"
            if (nonemptyInputs <= 0) or (fullCount >= fullCapacity):
                overallStatus = "idle"
        inputText = "All Full"
        inputStatus = "success"
        if (totalInputs <= 0) or (validInputs < totalInputs):
            inputText = f"{validInputs} / {totalInputs} Valid"
            inputStatus = "error"
            if self.valid:
                overallStatus = "paused"
        elif nonemptyInputs < totalInputs:
            inputText = f"{nonemptyInputs} / {totalInputs} Avail"
            inputStatus = "text-muted"
        elif fullInputs < totalInputs:
            inputText = f"{fullInputs} / {totalInputs} Full"
            inputStatus = "warning"
        outputRatio = 1
        outputColor = "text-muted"
        if (localCapacity <= 0) or (fullCapacity <= 0):
            outputRatio = 1
            outputColor = "error"
            if self.valid:
                overallStatus = "paused"
        elif localCount < localCapacity:
            outputRatio = fullCount / fullCapacity
            outputColor = "success"
        elif fullCount < fullCapacity:
            outputRatio = fullCount / fullCapacity
            outputColor = "warning"
        panel.status_dot(x + 12, y + 12, 4, overallStatus)
        x += 24
        panel.pill(x, y, inputText, inputStatus, size=24)
        x += 140
        panel.draw_text(x, y + 12, self.name, size=16)
        x = panel.width() - 80
        panel.progress_bar(x, y, 76, 24, outputRatio, outputColor)

    def drawDetailLine(self, panel: Panel, x, y, output):
        totalInputs = len(output.inputs)
        validInputs = 0
        nonemptyInputs = 0
        fullInputs = 0
        localCount = output.localCount()
        localCapacity = output.localCapacity()
        fullCount = output.fullCount()
        fullCapacity = output.fullCapacity()
        for itemId in output.inputs:
            if itemId not in self.inputs:
                continue
            status = self.inputs[itemId].status()
            if status <= INPUT_STATUS_INVALID:
                continue
            validInputs += 1
            if status <= INPUT_STATUS_EMPTY:
                continue
            nonemptyInputs += 1
            if status >= INPUT_STATUS_FULL:
                fullInputs += 1
        overallStatus = "error"
        if (totalInputs > 0) and (validInputs >= totalInputs):
            overallStatus = "idle"
            if (nonemptyInputs >= totalInputs) and (fullCount < fullCapacity):
                overallStatus = "running"
        inputText = "All Full"
        inputStatus = "success"
        if (totalInputs <= 0) or (validInputs < totalInputs):
            inputText = f"{validInputs} / {totalInputs} Valid"
            inputStatus = "error"
        elif nonemptyInputs < totalInputs:
            inputText = f"{nonemptyInputs} / {totalInputs} Avail"
            inputStatus = "text-muted"
        elif fullInputs < totalInputs:
            inputText = f"{fullInputs} / {totalInputs} Full"
            inputStatus = "warning"
        outputRatio = 1
        outputColor = "text-muted"
        if (localCapacity <= 0) or (fullCapacity <= 0):
            outputRatio = 1
            outputColor = "error"
        elif localCount < localCapacity:
            outputRatio = fullCount / fullCapacity
            outputColor = "success"
        elif fullCount < fullCapacity:
            outputRatio = fullCount / fullCapacity
            outputColor = "warning"
        panel.status_dot(x + 12, y + 12, 4, overallStatus)
        x += 24
        panel.pill(x, y, inputText, inputStatus, size=24)
        x += 140
        panel.draw_text(x, y + 12, output.name, size=16)
        x = panel.width() - 80
        panel.progress_bar(x, y, 76, 24, outputRatio, outputColor)

    def drawDetails(self, panel: Panel, x, y):
        for output in self.outputs:
            self.drawDetailLine(panel, x, y, output)
            y += 28


outposts = [ProductionOutpost(name) for name in production_map.PRODUCTION_SITES.keys()]
outposts.sort(key=lambda outpost: outpost.name)
outpostsByName = {outpost.name: outpost for outpost in outposts}
details = [OVERVIEW] + [o.name for o in outposts]

#TODO: call updateLinks (or maybe even regen outposts) every once in a while
while True:
    panel.clear()
    w = panel.width() - 2
    detailSel = panel.combo("details", 1, 0, w, details, default=OVERVIEW, size=28)
    y = 44
    panel.draw_text(24, 44, "Input", size=20)
    panel.draw_text(panel.width() - 80, 44, "Output", size=20)
    y += 10
    if detailSel != OVERVIEW:
        if (detailSel not in outpostsByName):
            continue
        panel.draw_text(164, 44, "Product", size=20)
        outpostsByName[detailSel].drawDetails(panel, 0, y)
        continue
    panel.draw_text(164, 44, "Outpost", size=20)
    for outpost in outposts:
        outpost.drawSummary(panel, 0, y)
        y += 28
