import scan_rover_utils

SCAN_START_IDX = 286
START_IDX_KEY = "rover_scan_idx"

notebook = get_component("notebook")
nocturna = get_component("nocturna")

rover = scan_rover_utils.ScanRoverHandler(self)

def doScan():
    startIdx = SCAN_START_IDX
    if notebook:
        startIdx = notebook.get(START_IDX_KEY, SCAN_START_IDX)
    scanPoints = rover.getScanPoints()
    for idx in range(startIdx, len(scanPoints)):
        (x, y) = scanPoints[idx]
        gotPoi = False
        for poi in nocturna.points_of_interest():
            if poi.scanned:
                continue
            dx = poi.x - x
            dy = poi.y - y
            if sqrt(dx * dx + dy * dy) <= self.sonar.range():
                gotPoi = True
                break
        if not gotPoi:
            print(f"Skipped point {idx} / {len(scanPoints)}")
            if notebook:
                notebook.set(START_IDX_KEY, idx + 1)
            continue
        rover.scanAt(x, y)
        print(f"Scanned point {idx} / {len(scanPoints)}")
        if notebook:
            notebook.set(START_IDX_KEY, idx + 1)

doScan()
