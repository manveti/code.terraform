import drill_rover_utils

SITE_COORDS = (750, 350)
HOME_COORDS = (710, 330)

rover = drill_rover_utils.DrillRoverHandler(self)
rover.mineLoop(SITE_COORDS, HOME_COORDS)
