import storage_utils

def _haveMaterials(recipe, count=1):
    for (material, needed) in recipe.inputs.items():
        needed *= count
        storage = storage_utils.getStorage(self.outpost, material)
        if (not storage) or (storage.count() < needed):
            return False
    return True

def prepareSmeltRun(recipe):
    result = self.set_recipe(recipe.id)
    if result.status != "ok":
        print(f"Couldn't set recipe {recipe.id}: {result.message}")
        return None
    storage = storage_utils.getStorage(self.outpost, recipe.output_item)
    storage.connect(self.output)
    return storage

def takeRecipe(recipe, count=1):
    if not _haveMaterials(recipe, count):
        return False
    for (material, needed) in recipe.inputs.items():
        needed *= count
        storage = storage_utils.getStorage(self.outpost, material)
        storage.connect(self.input)
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
    self.input.connect("")
    return True

def finishSmeltRun(recipe):
    while self.is_running():
        count = self.output.count()
        if count > 0:
            self.output.send(recipe.output_item, count)
        else:
            sleep(storage_utils.SLEEP_INTERVAL)
    count = self.output.count()
    while count > 0:
        result = self.output.send(recipe.output_item, count)
        if result.status in ("ok", "partial"):
            count -= result.moved
            continue
    self.output.connect("")

def smeltRun(recipe, count=1):
    if not prepareSmeltRun(recipe):
        return False
    if not takeRecipe(recipe, count):
        self.output.connect("")
        return False
    finishSmeltRun(recipe)
    return True

def smeltFull(recipe):
    size = sum(needed for needed in recipe.inputs.values())
    count = floor(self.input.capacity() / size)
    while (count > 1) and (not _haveMaterials(recipe, count)):
        count -= 1
    smeltRun(recipe, count)

def smeltBatch(recipe, count):
    if not prepareSmeltRun(recipe):
        return False
    size = sum(needed for needed in recipe.inputs.values())
    while count > 0:
        tookAction = False
        outputCount = self.output.count()
        if outputCount > 0:
            self.output.send(recipe.output_item, outputCount)
            tookAction = True
        inputSpace = self.input.capacity() - self.input.count()
        takeCount = min(floor(inputSpace / size), count)
        while (takeCount > 0) and (not _haveMaterials(recipe, takeCount)):
            takeCount -= 1
        if (takeCount > 0) and (takeRecipe(recipe, takeCount)):
            count -= takeCount
            tookAction = True
        if not tookAction:
            sleep(storage_utils.SLEEP_INTERVAL)
    finishSmeltRun(recipe)
    return True

def smeltOngoing(recipe):
    if not prepareSmeltRun(recipe):
        return False
    size = sum(needed for needed in recipe.inputs.values())
    while True:
        tookAction = False
        outputCount = self.output.count()
        if outputCount > 0:
            self.output.send(recipe.output_item, outputCount)
            tookAction = True
        inputSpace = self.input.capacity() - self.input.count()
        takeCount = floor(inputSpace / size)
        while (takeCount > 0) and (not _haveMaterials(recipe, takeCount)):
            takeCount -= 1
        if (takeCount > 0) and (takeRecipe(recipe, takeCount)):
            tookAction = True
        if not tookAction:
            sleep(storage_utils.SLEEP_INTERVAL)


#print(self.list_recipes())
#print(self.input.capacity())
recipe = self.find_recipe("smelt_iron_ingot")
smeltBatch(recipe, 23)


#####
##
# import prod_lib

# def smeltOneRecipe(recipe):
#     prod_lib.smeltOngoing(self, recipe)

# def smeltAllRecipes():
#     recipes = self.list_recipes()
#     idx = 0
#     while True:
#         prod_lib.smeltFull(self, recipes[idx])
#         idx = (idx + 1) % len(recipes)

# def smartSmelt():
#     recipes = self.list_recipes()
#     if len(recipes) == 1:
#         smeltOneRecipe(recipes[0])
#     else:
#         smeltAllRecipes()

# smartSmelt()
##
#####
