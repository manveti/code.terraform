import rover_utils

SITE_COORDS = (30, 30)

rover = rover_utils.DrillRoverHandler(self)

def mineOneSite():
    site = rover.getMiningSite(*SITE_COORDS)
    if not site:
        return
    while True:
        rover.mineAt(site)
        rover.waitForCharge()

mineOneSite()

# SCAN_START_IDX = 22
# START_IDX_KEY = "rover_scan_idx"

# notebook = get_component("notebook")

# def doScan():
#     startIdx = SCAN_START_IDX
#     if notebook:
#         startIdx = notebook.get(START_IDX_KEY, SCAN_START_IDX)
#     scanPoints = rover.getScanPoints()
#     for idx in range(startIdx, len(scanPoints)):
#         (x, y) = scanPoints[idx]
#         rover.scanAt(x, y)
#         print(f"Scanned point {idx} / {len(scanPoints)}")
#         if notebook:
#             notebook.set(START_IDX_KEY, idx + 1)

# #doScan()
# rover.goHome(1)