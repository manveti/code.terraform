while True:
    val = self.gauge()
    if (val >= self.next_window_low()) and (val <= self.next_window_high()):
        self.sync()