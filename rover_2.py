import drill_rover_utils

SITE_COORDS = (-190, 90)
HOME_COORDS = (-240, 110)

rover = drill_rover_utils.DrillRoverHandler(self)
rover.mineLoop(SITE_COORDS, HOME_COORDS)
