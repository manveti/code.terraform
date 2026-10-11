import cargo_rover_utils
import production_map
import storage_utils

HOME = "Iron Foundry"
PRODUCT = "iron_ingot"

rover = cargo_rover_utils.CargoRoverHandler(self)
source = storage_utils.getOutpost(HOME)
#dest = production_map.PRODUCTION_SITES[source.name].exports[PRODUCT]
dest = ("Construction Supplies",)
rover.freightLine(source, PRODUCT, dest)
