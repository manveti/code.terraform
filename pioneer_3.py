import drill_rover_utils

SITE_COORDS = (-140, 250)
HOME_COORDS = (-120, 230)

rover = drill_rover_utils.DrillRoverHandler(self)
rover.mineLoop(SITE_COORDS, HOME_COORDS)
