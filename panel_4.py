import production_map
import production_utils
import storage_utils

requester = production_utils.ProductionRequester()


class RecipeItem:
    def __init__(self, itemId, outpost, count):
        self.itemId = itemId
        self.name = production_map.itemName(itemId)
        self.outpost = outpost
        self.count = count
        self._storage = None
        #TODO: ...

    def getStorage(self):
        if (not self._storage) or (not self._storage.valid()):
            self._storage = storage_utils.getStorage(self.outpost, self.itemId)
        return self._storage


class ProductRecipe:
    def __init__(self, recipe, outpost):
        self.recipe = recipe
        self.outpost = outpost
        self.inputs = []
        for (itemId, count) in recipe.inputs.items():
            self.inputs.append(RecipeItem(itemId, outpost, count))
        for (port, count) in recipe.fluid_inputs.items():
            itemId = production_utils.portToItemId(port)
            self.inputs.append(RecipeItem(itemId, outpost, count))
        self.inputs.sort(key=lambda itm: itm.name)
        self.outputs = []
        if (recipe.byproduct_item) and (recipe.byproduct_count > 0):
            self.outputs.append(RecipeItem(recipe.byproduct_item, outpost, recipe.byproduct_count))
        if recipe.fluid_outputs:
            for (port, count) in recipe.fluid_outputs.items():
                itemId = production_utils.portToItemId(port)
                self.outputs.append(RecipeItem(itemId, outpost, count))
        self.outputs.sort(key=lambda itm: itm.name)
        self.outputs.insert(0, RecipeItem(recipe.output_item, outpost, recipe.output_count))

    @property
    def count(self):
        return self.recipe.output_count


class Product:
    def __init__(self, itemId, outpost):
        self.itemId = itemId
        self.name = production_map.itemName(itemId)
        self.outpost = storage_utils.getOutpost(outpost)
        self.recipe = None

    def getRecipe(self):
        if self.recipe:
            return self.recipe
        for building in self.outpost.buildings():
            building = get_component(building.id)
            if not hasattr(building, "list_recipes"):
                continue
            for recipe in building.list_recipes():
                if recipe.output_item == self.itemId:
                    self.recipe = ProductRecipe(recipe, self.outpost.name)
                    return self.recipe
        return None

    def drawInputs(self, panel: Panel, x, y, maxX):
        recipe = self.getRecipe()
        if not recipe:
            panel.draw_text(x, y + 12, "Recipe Unavailable", size=20, color="error")
            return None
        h = len(recipe.inputs) * 28 + 48
        panel.card(x, y, maxX - x, h, "Inputs")
        y += 34
        panel.draw_text(x + 2, y, "#", size=20)
        panel.draw_text(x + 30, y, "Item", size=20)
        panel.draw_text(maxX - 140, y, "Avail", size=20)
        panel.draw_text(maxX - 60, y, "Yield", size=20)
        y += 16
        for inputItem in recipe.inputs:
            panel.draw_text(x + 2, y + 12, str(inputItem.count), size=16)
            panel.draw_text(x + 30, y + 12, inputItem.name, size=16)
            recipeYield = 0
            ratio = 1
            status = "error"
            storage = inputItem.getStorage()
            if storage:
                recipeCount = inputItem.count
                storageCount = storage.count()
                if recipeCount > 0:
                    recipeYield = floor(storageCount / recipeCount) * recipe.count
                capacity = storage.capacity()
                if capacity > 0:
                    ratio = storageCount / capacity
                    if ratio >= 0.5:
                        status = "success"
                    elif storageCount >= recipeCount:
                        status = "warning"
            panel.progress_bar(maxX - 140, y, 72, 24, ratio, status)
            panel.draw_text(maxX - 60, y + 12, str(recipeYield))
            y += 28
        return h + 1

    def drawOutputs(self, panel: Panel, x, y, maxX):
        recipe = self.getRecipe()
        if not recipe:
            return 0
        h = len(recipe.outputs) * 28 + 48
        panel.card(x, y, maxX - x, h, "Outputs")
        y += 34
        panel.draw_text(x + 2, y, "#", size=20)
        panel.draw_text(x + 30, y, "Item", size=20)
        panel.draw_text(maxX - 140, y, "Avail", size=20)
        panel.draw_text(maxX - 60, y, "Yield", size=20)
        y += 16
        for outputItem in recipe.outputs:
            panel.draw_text(x + 2, y + 12, str(outputItem.count), size=16)
            panel.draw_text(x + 30, y + 12, outputItem.name, size=16)
            recipeYield = 0
            ratio = 1
            status = "error"
            storage = outputItem.getStorage()
            if storage:
                recipeCount = outputItem.count
                storageCount = storage.count()
                capacity = storage.capacity()
                if capacity > 0:
                    ratio = storageCount / capacity
                    freeCount = capacity - storageCount
                    if storageCount >= capacity:
                        status = "text-muted"
                    elif ratio >= 0.8:
                        status = "warning"
                    elif freeCount > recipeCount:
                        status = "success"
                    if recipeCount > 0:
                        recipeYield = floor(freeCount / recipeCount) * recipe.count
            panel.progress_bar(maxX - 140, y, 72, 24, ratio, status)
            panel.draw_text(maxX - 60, y + 12, str(recipeYield))
            y += 28
        return h + 1

    def drawRequests(self, panel: Panel, x, y, maxX):
        comms = requester.getComms()
        if not comms:
            return
        count = 0
        for msg in comms.pending(production_utils.CHANNEL):
            if msg.value.get("item") == self.itemId:
                count += msg.value.get("count", 0)
        panel.draw_text(x, y + 12, f"Pending Requests: {count}", size=20)
        clearReqs = panel.button("do_clear_request", maxX - 92, y, label="Clear")
        y += 28
        reqStr = panel.text_field("request_count", maxX - 196, y, 100, placeholder="#", size=24)
        reqCount = 0
        try:
            reqCount = int(reqStr)
        except ValueError:
            pass
        requested = panel.button("do_request", maxX - 92, y, label="Request")
        if (clearReqs) and (count > 0):
            requester.cancelProduction(self.itemId)
        if (not requested) or (reqCount <= 0):
            return
        panel.set_text("request_count", "")
        requester.requestProduction(self.itemId, reqCount)
    
    def drawPanel(self, panel: Panel, x, y, maxX, maxY):
        panel.clip_rect(x, y, maxX - x, maxY - y - 56)
        panel.draw_text(x, y + 12, f"Produced at {self.outpost.name}", size=16)
        y += 24
        h = self.drawInputs(panel, x, y, maxX)
        if h is None:
            return
        y += h
        h = self.drawOutputs(panel, x, y, maxX)
        if h is None:
            return
        panel.clear_clip()
        self.drawRequests(panel, x, maxY - 56, maxX)


products = []
for (outpostName, site) in production_map.PRODUCTION_SITES.items():
    products.extend(Product(itemId, outpostName) for itemId in site.onDemand)
products.sort(key=lambda product: product.name)
productNames = [product.name for product in products]
productsByName = {product.name: product for product in products}

while True:
    panel.clear()
    w = panel.width()
    productName = panel.combo("product", 1, 0, w - 2, productNames, size=28)
    product = productsByName.get(productName)
    if not product:
        continue
    product.drawPanel(panel, 0, 32, w, panel.height())
