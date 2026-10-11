import drill_rover_utils

SITE_COORDS = (-450, 120)
HOME_COORDS = (-420, 130)

rover = drill_rover_utils.DrillRoverHandler(self)
rover.mineLoop(SITE_COORDS, HOME_COORDS)