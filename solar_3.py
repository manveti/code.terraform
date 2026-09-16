clock = get_component("clock")

while True:
    elev = clock.get_elevation()
    self.set_tilt(90 - elev)