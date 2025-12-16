import random, json, os, fcntl
from flask import current_app

dbs2_data = []
dbs2_list = [
    {"name": "passwords", "data": [
        "backendintegration"
    ]},
    {"name": "inventory", "data": []},
]


def get_dbs2_file():
    # Always use Flask app.config['DATA_FOLDER'] for shared data
    data_folder = current_app.config['DATA_FOLDER']
    return os.path.join(data_folder, 'dbs2_data.json')


def _read_dbs2_file():
    DBS2_FILE = get_dbs2_file()
    if not os.path.exists(DBS2_FILE):
        return []
    with open(DBS2_FILE, 'r') as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            data = json.load(f)
        except Exception:
            data = []
        fcntl.flock(f, fcntl.LOCK_UN)
    return data


def _write_dbs2_file(data):
    DBS2_FILE = get_dbs2_file()
    with open(DBS2_FILE, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(data, f)
        fcntl.flock(f, fcntl.LOCK_UN)


def initDBS2():
    DBS2_FILE = get_dbs2_file()
    # Only initialize if file does not exist
    if os.path.exists(DBS2_FILE):
        return
    dbs2_data = []
    item_id = 0
    for item in dbs2_list:
        dbs2_data.append({
            "id": item_id,
            "name": item["name"],
            "description": item.get("description", ""),
            "data": item.get("data", [])
        })
        item_id += 1
    _write_dbs2_file(dbs2_data)


def getDBS2Items():
    return _read_dbs2_file()


def getDBS2Item(id):
    items = _read_dbs2_file()
    return items[id]


def getRandomDBS2Item():
    items = _read_dbs2_file()
    return random.choice(items) if items else None


def printDBS2Item(item):
    print(item.get('id'), item.get('name'))
    print("Description:", item.get('description', ""))


def countDBS2Items():
    items = _read_dbs2_file()
    return len(items)


if __name__ == "__main__":
    initDBS2()  # initialize DBS2 data

    # Random item
    print("Random item")
    item = getRandomDBS2Item()
    if item:
        printDBS2Item(item)

    # Count of items
    print("DBS2 Items Count: " + str(countDBS2Items()))