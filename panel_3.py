SOLAR_OUTPUT = 19.5
DAY_START = 0
SOLAR_RISE_START = 6
SOLAR_RISE_HALF = 7
SOLAR_RISE_FULL = 9
SOLAR_FALL_START = 13
SOLAR_FALL_HALF = 17
SOLAR_FALL_FULL = 20
DAY_END = 24
SOLAR_GENERATOR_TYPES = ("solar_generator",)
CONSUMABLE_GENERATORS = {
    "oil_generator": 700,
    "reactor": 5000,
    "steam_turbine": 108,
}
SI_PREFIXES = ("k", "M", "G", "T", "P", "E", "Z", "Y", "R", "Q")

clock = get_component("clock")
power = get_component("power_control")

def getTimestamp():
    (h, m, s) = clock.get_time()
    return h + (m / 60) + (s / 3600)

def roundStandard(x):
    return floor(x + 0.5)

def formatSI(x):
    curPrefix = ""
    for prefix in SI_PREFIXES:
        if x < 1000:
            break
        x /= 1000
        curPrefix = prefix
    if x < 10:
        x = roundStandard(x * 10) / 10
    else:
        x = roundStandard(x)
    return f"{x}{curPrefix}"


class GridWrapper:
    def __init__(self, grid: PowerGrid):
        self.timestamp = getTimestamp()
        self.name = "Unnamed"
        self.grid = grid
        self.outposts = []
        for outpostId in grid.outpost_ids:
            outpost = get_component(outpostId)
            self.outposts.append(outpost.name())
        self.outposts.sort()
        if self.outposts:
            self.name = self.outposts[0]
        self.solarCapacity = 0
        self.consumableCapacity = 0
        for member in grid.members:
            if member.type_id in SOLAR_GENERATOR_TYPES:
                self.solarCapacity += SOLAR_OUTPUT
                continue
            if member.type_id in CONSUMABLE_GENERATORS:
                self.consumableCapacity += CONSUMABLE_GENERATORS[member.type_id]
                continue
        self.totalCapacity = self.solarCapacity + self.consumableCapacity

    @property
    def produced(self):
        return int(self.grid.generated)

    @property
    def solar(self):
        return int(self.solarCapacity)

    @property
    def consumed(self):
        return int(self.grid.consumed)

    @property
    def curBat(self):
        return formatSI(self.grid.stored) + "Wh"

    @property
    def maxBat(self):
        return formatSI(self.grid.capacity) + "Wh"

    def solarAtTime(self, t):
        if (t <= SOLAR_RISE_START) or (t >= SOLAR_FALL_FULL):
            return 0
        if t <= SOLAR_RISE_HALF:
            eff = (t - SOLAR_RISE_START) / (SOLAR_RISE_HALF - SOLAR_RISE_START)
            eff *= 0.5
            return eff * self.solarCapacity
        if t < SOLAR_RISE_FULL:
            eff = (t - SOLAR_RISE_HALF) / (SOLAR_RISE_FULL - SOLAR_RISE_HALF)
            eff *= 0.5
            eff += 0.5
            return eff * self.solarCapacity
        if t <= SOLAR_FALL_START:
            return self.solarCapacity
        if t <= SOLAR_FALL_HALF:
            eff = (SOLAR_FALL_HALF - t) / (SOLAR_FALL_HALF - SOLAR_FALL_START)
            eff *= 0.5
            eff += 0.5
            return eff * self.solarCapacity
        # t between SOLAR_FALL_HALF and SOLAR_FALL_FULL
        eff = (SOLAR_FALL_FULL - t) / (SOLAR_FALL_FULL - SOLAR_FALL_HALF)
        eff *= 0.5
        return eff * self.solarCapacity

    def nextSolarMatch(self, consumed):
        if (consumed > self.solarCapacity) or (self.solarCapacity <= 0):
            return None
        eff = consumed / self.solarCapacity
        if eff >= 1:
            return SOLAR_RISE_FULL
        if eff >= 0.5:
            offset = (eff - 0.5) * (SOLAR_RISE_FULL - SOLAR_RISE_HALF)
            return SOLAR_RISE_HALF + offset
        return SOLAR_RISE_START + (eff * (SOLAR_RISE_HALF - SOLAR_RISE_START))

    def surplusNeeded(self, consumed):
        if consumed <= self.solarAtTime(self.timestamp):
            return 0
        matchTime = self.nextSolarMatch(consumed)
        if matchTime is None:
            return None
        t = self.timestamp
        need = 0
        done = False
        if (t >= SOLAR_FALL_START) and (t < SOLAR_FALL_HALF):
            nextT = SOLAR_FALL_HALF
            if (matchTime > t) and (matchTime < SOLAR_FALL_HALF):
                nextT = matchTime
                done = True
            dT = nextT - t
            solar = self.solarAtTime(t + (dT * 0.5))
            need += (consumed - solar) * dT
            if done:
                return need
            t = nextT
        if (t >= SOLAR_FALL_HALF) and (t < SOLAR_FALL_FULL):
            nextT = SOLAR_FALL_FULL
            if (matchTime > t) and (matchTime < SOLAR_FALL_FULL):
                nextT = matchTime
                done = True
            dT = nextT - t
            solar = self.solarAtTime(t + (dT * 0.5))
            need += (consumed - solar) * dT
            if done:
                return need
            t = nextT
        if t >= SOLAR_FALL_FULL:
            nextT = DAY_END
            if (matchTime > t) and (matchTime < SOLAR_FALL_FULL):
                nextT = matchTime
                done = True
            dT = nextT - t
            need += consumed * dT
            if done:
                return need
            t = DAY_START
        if t < SOLAR_RISE_START:
            nextT = SOLAR_RISE_START
            if (matchTime > t) and (matchTime < SOLAR_FALL_FULL):
                nextT = matchTime
                done = True
            dT = nextT - t
            need += consumed * dT
            if done:
                return need
            t = nextT
        if t < SOLAR_RISE_HALF:
            nextT = SOLAR_RISE_HALF
            if (matchTime > t) and (matchTime < SOLAR_RISE_HALF):
                nextT = matchTime
                done = True
            dT = nextT - t
            solar = self.solarAtTime(t + (dT * 0.5))
            need += (consumed - solar) * dT
            if done:
                return need
            t = nextT
        if t > SOLAR_RISE_FULL:
            # shouldn't be able to get here, but if we do power gen is too low
            return None
        nextT = SOLAR_RISE_FULL
        if (matchTime > t) and (matchTime < SOLAR_RISE_FULL):
            nextT = matchTime
        dT = nextT - t
        solar = self.solarAtTime(t + (dT * 0.5))
        need += (consumed - solar) * dT
        return need

    def drawStatus(self, panel: Panel, x, y):
        overallStatus = "running"
        batProgress = 1
        batStatus = "error"
        if self.grid.capacity > 0:
            batProgress = self.grid.stored / self.grid.capacity
            if self.grid.stored <= 0:
                overallStatus = "idle"
                batStatus = "text-muted"
            if self.grid.generated >= self.grid.consumed:
                needed = 0
            else:
                needed = self.surplusNeeded(self.grid.consumed)
            if (needed is not None) and (needed <= self.grid.stored):
                # enough to get through the night on battery alone
                batStatus = "success"
            else:
                if self.grid.generated >= self.grid.consumed:
                    needed = 0
                else:
                    needed = self.surplusNeeded(self.grid.consumed - self.consumableCapacity)
                if (needed is not None) and (needed <= self.grid.stored):
                    # enough to get through the night with consumable generators
                    batStatus = "warning"
        if self.grid.consumed >= self.totalCapacity:
            overallStatus = "error"
        if self.grid.consumed >= self.solarCapacity:
            overallStatus = "paused"
        panel.status_dot(x + 12, y + 12, 4, overallStatus)
        x += 24
        outpostX = x
        panel.draw_text(x, y + 12, self.name, size=16)
        x = panel.width() - 250
        panel.draw_text(x, y + 12, f"{self.produced}W", size=16)
        x += 60
        panel.draw_text(x, y + 12, f"{self.solar}W", size=16)
        x += 60
        panel.draw_text(x, y + 12, f"{self.consumed}W", size=16)
        x += 60
        panel.progress_bar(x, y, 67, 10, batProgress, batStatus)
        panel.draw_text(x, y + 16, f"{self.curBat} / {self.maxBat}", size=8)
        for outpost in self.outposts[1:]:
            y += 28
            panel.draw_text(outpostX, y + 12, outpost, size=16)
        return len(self.outposts) or 1

# power dashboard: for each power network, list outposts and status
#   for grid in get_component("power_control").grids() //see also .set_powered(machine_id, on)
#     grid.outpost_ids is list<string> of outpost ids in this grid
#     grid.machine_ids is list<string> of machine ids in this grid
#     grid.members is list<PowerGridMember> for every building in this grid
#       .id, .name, .type_id, .outpost_id (may be ""), .powered (bool), .generated, .consumed, .stored, .capacity
#         "generator" in .roles means member can generate power
#         type_id=="solar_generator": 19.5W average, free
#           solar ramps up from 0-25W from 0600 to 0700, from 25-50W until 0900, sustains 50W until 1300, drops 50-25W until 1700, from 25-0W until 2000
#         type_id==?"steam_turbine"?: <=108W, consumes steam 90t/h (throttle scales both linearly)
#         type_id==?"oil_generator"?: <=700W, consumes oil 8t/h (throttle scales both linearly)
#         type_id==?"reactor"?: <=5kW, consumes fuel rods 1/72h and water .5-1t/h (heat scales down fuel use; power output and water use unclear)
#     grid.generated, .consumed, .net, .stored, .capacity
#   [overall status] [outpost name] [prod] [sol] [cons] [bat]
#     prod = grid.generated; sol = 19.5 * # of solar generators; cons = grid.consumed; bat = grid.stored / grid.capacity; fuel = stored/max fuel
#     #want: overall status: grey if dead, red if not enough total power, yellow if not enough solar power, green if good
#     #      battery status: grey if dead, red if not enough to get through night, yellow if not enough to get through night on bat alone, green if good
#     grid.stored <= 0 => overall status grey
#     grid.consumed >= total generation capacity => overall status red
#     (grid.net < 0) and (-grid.net * hours_to_0600 >= grid.stored) => overall status red, battery status red



#     def drawSummary(self, pane: Panel, x, y):
#         overallStatus = "error"
#         if self.valid:
#             overallStatus = "running"
#             if (nonemptyInputs <= 0) or (fullCount >= fullCapacity):
#                 overallStatus = "idle"
#         inputText = "All Full"
#         inputStatus = "success"
#         if (totalInputs <= 0) or (validInputs < totalInputs):
#             inputText = f"{validInputs} / {totalInputs} Valid"
#             inputStatus = "error"
#             if self.valid:
#                 overallStatus = "paused"
#         elif nonemptyInputs < totalInputs:
#             inputText = f"{nonemptyInputs} / {totalInputs} Avail"
#             inputStatus = "text-muted"
#         elif fullInputs < totalInputs:
#             inputText = f"{fullInputs} / {totalInputs} Full"
#             inputStatus = "warning"
#         outputRatio = 1
#         outputColor = "text-muted"
#         if (localCapacity <= 0) or (fullCapacity <= 0):
#             outputRatio = 1
#             outputColor = "error"
#             if self.valid:
#                 overallStatus = "paused"
#         elif localCount < localCapacity:
#             outputRatio = fullCount / fullCapacity
#             outputColor = "success"
#         elif fullCount < fullCapacity:
#             outputRatio = fullCount / fullCapacity
#             outputColor = "warning"
#         panel.status_dot(x + 12, y + 12, 4, overallStatus)
#         x += 24
#         panel.pill(x, y, inputText, inputStatus, size=24)
#         x += 140
#         panel.draw_text(x, y + 12, self.name, size=16)
#         x = panel.width() - 80
#         panel.progress_bar(x, y, 76, 24, outputRatio, outputColor)

#     def drawDetailLine(self, panel: Panel, x, y, output):
#         totalInputs = len(output.inputs)
#         validInputs = 0
#         nonemptyInputs = 0
#         fullInputs = 0
#         localCount = output.localCount()
#         localCapacity = output.localCapacity()
#         fullCount = output.fullCount()
#         fullCapacity = output.fullCapacity()
#         for itemId in output.inputs:
#             if itemId not in self.inputs:
#                 continue
#             status = self.inputs[itemId].status()
#             if status <= INPUT_STATUS_INVALID:
#                 continue
#             validInputs += 1
#             if status <= INPUT_STATUS_EMPTY:
#                 continue
#             nonemptyInputs += 1
#             if status >= INPUT_STATUS_FULL:
#                 fullInputs += 1
#         overallStatus = "error"
#         if (totalInputs > 0) and (validInputs >= totalInputs):
#             overallStatus = "idle"
#             if (nonemptyInputs >= totalInputs) and (fullCount < fullCapacity):
#                 overallStatus = "running"
#         inputText = "All Full"
#         inputStatus = "success"
#         if (totalInputs <= 0) or (validInputs < totalInputs):
#             inputText = f"{validInputs} / {totalInputs} Valid"
#             inputStatus = "error"
#         elif nonemptyInputs < totalInputs:
#             inputText = f"{nonemptyInputs} / {totalInputs} Avail"
#             inputStatus = "text-muted"
#         elif fullInputs < totalInputs:
#             inputText = f"{fullInputs} / {totalInputs} Full"
#             inputStatus = "warning"
#         outputRatio = 1
#         outputColor = "text-muted"
#         if (localCapacity <= 0) or (fullCapacity <= 0):
#             outputRatio = 1
#             outputColor = "error"
#         elif localCount < localCapacity:
#             outputRatio = fullCount / fullCapacity
#             outputColor = "success"
#         elif fullCount < fullCapacity:
#             outputRatio = fullCount / fullCapacity
#             outputColor = "warning"
#         panel.status_dot(x + 12, y + 12, 4, overallStatus)
#         x += 24
#         panel.pill(x, y, inputText, inputStatus, size=24)
#         x += 140
#         panel.draw_text(x, y + 12, output.name, size=16)
#         x = panel.width() - 80
#         panel.progress_bar(x, y, 76, 24, outputRatio, outputColor)

#     def drawDetails(self, panel: Panel, x, y):
#         for output in self.outputs:
#             self.drawDetailLine(panel, x, y, output)
#             y += 28


# outposts = [ProductionOutpost(name) for name in production_map.PRODUCTION_SITES.keys()]
# outposts.sort(key=lambda outpost: outpost.name)
# outpostsByName = {outpost.name: outpost for outpost in outposts}
# details = [OVERVIEW] + [o.name for o in outposts]

while True:
    panel.clear()
    panel.draw_text(24, 12, "Outpost", size=20)
    w = panel.width()
    panel.draw_text(w - 250, 12, "Prod", size=20)
    panel.draw_text(w - 190, 12, "Sol", size=20)
    panel.draw_text(w - 130, 12, "Cons", size=20)
    panel.draw_text(w - 70, 12, "Bat", size=20)
    grids = [GridWrapper(grid) for grid in power.grids()]
    grids.sort(key=lambda grid: grid.name)
    x = 0
    y = 22
    for grid in grids:
        rows = grid.drawStatus(panel, x, y)
        y += rows * 28
#   [overall status] [outpost name] [prod] [sol] [cons] [bat]
# #TODO: call updateLinks (or maybe even regen outposts) every once in a while
# while True:
#     panel.clear()
#     w = panel.width() - 2
#     detailSel = panel.combo("details", 1, 0, w, details, default=OVERVIEW, size=28)
#     y = 44
#     panel.draw_text(24, 44, "Input", size=20)
#     panel.draw_text(panel.width() - 80, 44, "Output", size=20)
#     y += 10
#     if detailSel != OVERVIEW:
#         if (detailSel not in outpostsByName):
#             continue
#         panel.draw_text(164, 44, "Product", size=20)
#         outpostsByName[detailSel].drawDetails(panel, 0, y)
#         continue
#     panel.draw_text(164, 44, "Outpost", size=20)
#     for outpost in outposts:
#         outpost.drawSummary(panel, 0, y)
#         y += 28
