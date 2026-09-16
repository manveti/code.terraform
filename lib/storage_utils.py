HUMAN_SLEEP_INTERVAL = 10
SLEEP_INTERVAL = 0.1

def formatStorage(item):
    return f"storage_bin_{item}"

def getStorage(name):
    storage = get_component_by_name(name)
    if not storage:
        notify(f"Missing storage: {name}", "info", 0)
    while not storage:
        sleep(HUMAN_SLEEP_INTERVAL)
        storage = get_component_by_name(name)
    return storage

def connectStorage(pipe, storage):
    pipe.connect(storage.id)
    while pipe.connected_id() != storage.id:
        sleep(SLEEP_INTERVAL)
        pipe.connect(storage.id)

def connectStorageName(pipe, name):
    storage = getStorage(name)
    connectStorage(pipe, storage)