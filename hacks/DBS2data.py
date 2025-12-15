import random, json, os, fcntl
from flask import current_app

dbs2_data = []
dbs2_list = [
    {"name": "passwords", "data": [
        "ishowgreen",
        "helloworld",
        "albuquerque",
        "ilovebitcoin",
        "cryptorules",
        "unemployment",
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
            "description": item["description"],
            "likes": 0, 
            "dislikes": 0
        })
        item_id += 1
    # Prime some likes and dislikes
    for i in range(3):
        id = random.choice(dbs2_data)['id']
        dbs2_data[id]['likes'] += 1
    for i in range(2):
        id = random.choice(dbs2_data)['id']
        dbs2_data[id]['dislikes'] += 1
    _write_dbs2_file(dbs2_data)
        
def getDBS2Items():
    return _read_dbs2_file()

def getDBS2Item(id):
    items = _read_dbs2_file()
    return items[id]

def getRandomDBS2Item():
    items = _read_dbs2_file()
    return random.choice(items)

def favoriteDBS2Item():
    items = _read_dbs2_file()
    best = 0
    bestID = -1
    for item in items:
        if item['likes'] > best:
            best = item['likes']
            bestID = item['id']
    return items[bestID] if bestID != -1 else None
    
def dislikedDBS2Item():
    items = _read_dbs2_file()
    worst = 0
    worstID = -1
    for item in items:
        if item['dislikes'] > worst:
            worst = item['dislikes']
            worstID = item['id']
    return items[worstID] if worstID != -1 else None


# Atomic vote update with exclusive lock
def _vote_dbs2(id, field):
    DBS2_FILE = get_dbs2_file()
    with open(DBS2_FILE, 'r+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        items = json.load(f)
        items[id][field] += 1
        # Move file pointer to start before writing updated JSON
        f.seek(0)
        json.dump(items, f)
        # Truncate file to remove any leftover data from previous content
        f.truncate()
        fcntl.flock(f, fcntl.LOCK_UN)
    return items[id][field]

def addDBS2Like(id):
    return _vote_dbs2(id, 'likes')

def addDBS2Dislike(id):
    return _vote_dbs2(id, 'dislikes')

def printDBS2Item(item):
    print(item['id'], item['name'], "\n", "Description:", item['description'], "\n", "Likes:", item['likes'], "\n", "Dislikes:", item['dislikes'], "\n")

def countDBS2Items():
    items = _read_dbs2_file()
    return len(items)

if __name__ == "__main__": 
    initDBS2()  # initialize DBS2 data
    
    # Most liked and most disliked
    best = favoriteDBS2Item()
    if best:
        print("Most liked:", best['likes'])
        printDBS2Item(best)
    worst = dislikedDBS2Item()
    if worst:
        print("Most disliked:", worst['dislikes'])
        printDBS2Item(worst)
    
    # Random item
    print("Random item")
    printDBS2Item(getRandomDBS2Item())
    
    # Count of items
    print("DBS2 Items Count: " + str(countDBS2Items()))