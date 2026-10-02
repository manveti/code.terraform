import production_utils

producer = production_utils.ProducerHandler(self)
#print(producer.getRecipes())

recipe = self.find_recipe("smelt_titanium_ingot")
producer.productionRun(recipe, 93)