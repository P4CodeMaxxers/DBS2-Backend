import random, json, os, fcntl
from flask import current_app

dbs2_data = []
dbs2_list = [
    {"name": "passwords", "data": [
        "ishowgreen",
        "cryptoking", 
        "basement",
        "password",
        "helloworld"
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
    if 0 <= id < len(items):
        return items[id]
    return None


def getDBS2ItemByName(name):
    """Get item by name (e.g., 'passwords')"""
    items = _read_dbs2_file()
    for item in items:
        if item.get('name', '').lower() == name.lower():
            return item
    return None


def updateDBS2Item(id, data):
    """Update an item by ID"""
    items = _read_dbs2_file()
    if 0 <= id < len(items):
        # Update fields
        if 'data' in data:
            items[id]['data'] = data['data']
        if 'description' in data:
            items[id]['description'] = data['description']
        if 'name' in data:
            items[id]['name'] = data['name']
        _write_dbs2_file(items)
        return items[id]
    return None


def updateDBS2ItemByName(name, data):
    """Update an item by name"""
    items = _read_dbs2_file()
    for i, item in enumerate(items):
        if item.get('name', '').lower() == name.lower():
            if 'data' in data:
                items[i]['data'] = data['data']
            if 'description' in data:
                items[i]['description'] = data['description']
            _write_dbs2_file(items)
            return items[i]
    return None


def getPasswords():
    """Get the global passwords list (always returns 5)"""
    DEFAULT_PASSWORDS = ["ishowgreen", "cryptoking", "basement", "password", "helloworld"]
    
    item = getDBS2ItemByName('passwords')
    if item and 'data' in item and len(item['data']) > 0:
        passwords = item['data']
        # Ensure we have at least 5 passwords
        while len(passwords) < 5:
            # Add defaults that aren't already in the list
            for dp in DEFAULT_PASSWORDS:
                if dp not in passwords and len(passwords) < 5:
                    passwords.append(dp)
            # If still not enough, add numbered versions
            if len(passwords) < 5:
                passwords.append(f"password{len(passwords)}")
        return passwords[:5]
    
    # Initialize with defaults if empty
    updatePasswords(DEFAULT_PASSWORDS)
    return DEFAULT_PASSWORDS


def updatePasswords(passwords):
    """Update the global passwords list (max 5)"""
    # Limit to 5 passwords
    passwords = passwords[:5] if len(passwords) > 5 else passwords
    
    items = _read_dbs2_file()
    found = False
    for i, item in enumerate(items):
        if item.get('name', '').lower() == 'passwords':
            items[i]['data'] = passwords
            found = True
            break
    
    if not found:
        # Create passwords entry if it doesn't exist
        items.append({
            "id": len(items),
            "name": "passwords",
            "description": "Global passwords for Infinite User minigame",
            "data": passwords
        })
    
    _write_dbs2_file(items)
    return passwords


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