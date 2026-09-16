therm = get_component("thermometer")
trans = get_component("transmitter")

trans.connect("earth")
trans.transmit("current_temperature", therm.get_value())