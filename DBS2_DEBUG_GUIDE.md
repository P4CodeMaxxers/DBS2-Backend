# DBS2 Backend Testing & Debugging Guide

---

# Table of Contents
1. [What Is This System?](#1-what-is-this-system)
2. [Key Vocabulary](#2-key-vocabulary)
3. [Setting Up For Testing](#3-setting-up-for-testing)
4. [Testing with Postman](#4-testing-with-postman)
5. [Testing with Frontend](#5-testing-with-frontend)
6. [Using the Admin Dashboard](#6-using-the-admin-dashboard)
7. [Common Errors & Fixes](#7-common-errors--fixes)
8. [AP CSP Exam Connections](#8-ap-csp-exam-connections)
9. [Quick Reference Cheat Sheet](#9-quick-reference-cheat-sheet)

---

# 1. What Is This System?

## The Big Picture

Think of this like a video game save system:

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   YOU (Player)  │ ──────▶ │     SERVER      │ ──────▶ │    DATABASE     │
│   Playing Game  │         │  (Flask/Python) │         │    (SQLite)     │
│                 │ ◀────── │                 │ ◀────── │                 │
│  See your crypto│         │ Processes data  │         │ Stores data     │
└─────────────────┘         └─────────────────┘         └─────────────────┘
     Frontend                    Backend                    Storage
    (JavaScript)                (Python)                   (Database)
```

**What gets saved for each player:**
- 💰 Crypto (in-game currency)
- 🎒 Inventory (items you collect)
- 🏆 High Scores (best scores per minigame)
- ✅ Completion Status (which minigames you've beaten)

## How Login Works (Important!)

1. You type username/password on the login page
2. Server checks if they're correct
3. If yes, server creates a **session** and sends a **cookie** to your browser
4. Your browser automatically sends this cookie with EVERY future request
5. Server reads the cookie and knows who you are

**Think of it like a wristband at an amusement park** - once you get it at the entrance, you don't need to show your ticket again for every ride.

---

# 2. Key Vocabulary

| Term | Simple Explanation | Example |
|------|-------------------|---------|
| **API** | A way for programs to talk to each other | Your game asks the server "what's my crypto?" |
| **Endpoint** | A specific URL that does something | `/api/dbs2/crypto` gets your crypto balance |
| **GET** | Asking for information | "What's my inventory?" |
| **POST** | Creating something new | "Add this item to my inventory" |
| **PUT** | Updating something existing | "Change my crypto to 500" |
| **DELETE** | Removing something | "Remove item #2 from inventory" |
| **JSON** | A format for sending data | `{"crypto": 500, "name": "West"}` |
| **Cookie** | Small data stored in browser | Remembers you're logged in |
| **Session** | Server's memory of who you are | Links your cookie to your account |
| **Database** | Where all data is permanently stored | Like a spreadsheet that saves forever |
| **Model** | Code that defines data structure | "A player has crypto, inventory, scores..." |
| **Blueprint** | Group of related API endpoints | All `/api/dbs2/*` routes together |

---

# 3. Setting Up For Testing

## Step 1: Make Sure Server Is Running

Open terminal in your project folder and run:
```bash
python main.py
```

You should see:
```
** Server running: http://localhost:8587
DBS2 Players initialized with test users: West, Cyrus, Maya
```

**If you see errors:**
- `ModuleNotFoundError` → Run `pip install flask flask-login flask-restful`
- `Address already in use` → Another server is running, close it first
- Database errors → Delete your `.db` file and restart

## Step 2: Know Your Test Accounts

| Username | Password | Crypto | Minigames Done |
|----------|----------|--------|----------------|
| `west` | `dbs2test` | 1250 | 5/5 (all complete) |
| `cyrus` | `dbs2test` | 980 | 3/5 |
| `maya` | `dbs2test` | 750 | 2/5 |

## Step 3: Install Postman

1. Go to https://www.postman.com/downloads/
2. Download and install (free version is fine)
3. Create an account or skip sign-in

---

# 4. Testing with Postman

Postman lets you send requests to your API without using a browser. This is how backend developers test their code!

## 4.1 First: Login to Get a Cookie

### Step-by-Step:

1. **Open Postman**

2. **Create a new request:**
   - Click the `+` button for a new tab
   - Change `GET` to `POST` (dropdown on the left)
   - Enter URL: `http://localhost:8001/login`

3. **Set up the login data:**
   - Click the `Body` tab (below the URL)
   - Select `x-www-form-urlencoded`
   - Add these key-value pairs:
     ```
     Key: username    Value: west
     Key: password    Value: dbs2test
     ```

4. **Send the request:**
   - Click the blue `Send` button
   - You should see HTML response (the homepage)

5. **Verify cookie was saved:**
   - Click the `Cookies` link (below Send button)
   - You should see a `session` cookie for `localhost`

**Screenshot of what it should look like:**
```
┌─────────────────────────────────────────────────────────────┐
│ POST ▼ │ http://localhost:8887/login          │ Send │     │
├─────────────────────────────────────────────────────────────┤
│ Params │ Auth │ Headers │ Body ● │ Pre-req │ Tests │       │
├─────────────────────────────────────────────────────────────┤
│ ○ none  ○ form-data  ● x-www-form-urlencoded  ○ raw       │
├─────────────────────────────────────────────────────────────┤
│ KEY             │ VALUE                                     │
│ username        │ west                                      │
│ password        │ dbs2test                                  │
└─────────────────────────────────────────────────────────────┘
```

## 4.2 Test Each API Endpoint

Now that you're "logged in" (Postman has your cookie), test each endpoint:

### GET Your Player Data
```
Method: GET
URL: http://localhost:8887/api/dbs2/player
Body: (none needed)
```

**Expected Response:**
```json
{
    "id": 1,
    "user_id": 1,
    "user_info": {
        "uid": "west",
        "name": "West"
    },
    "crypto": 1250,
    "inventory": [...],
    "scores": {...},
    "completed_ash_trail": true,
    ...
}
```

### GET Your Crypto Balance
```
Method: GET
URL: http://localhost:8887/api/dbs2/crypto
```

**Expected Response:**
```json
{
    "crypto": 1250
}
```

### PUT (Update) - Add Crypto
```
Method: PUT
URL: http://localhost:8887/api/dbs2/crypto
Headers: Content-Type: application/json
Body (raw JSON):
{
    "add": 100
}
```

**Expected Response:**
```json
{
    "crypto": 1350
}
```

### PUT - Set Crypto to Specific Value
```
Method: PUT
URL: http://localhost:8887/api/dbs2/crypto
Headers: Content-Type: application/json
Body (raw JSON):
{
    "crypto": 500
}
```

### GET Your Inventory
```
Method: GET
URL: http://localhost:8887/api/dbs2/inventory
```

### POST - Add Item to Inventory
```
Method: POST
URL: http://localhost:8887/api/dbs2/inventory
Headers: Content-Type: application/json
Body (raw JSON):
{
    "name": "Secret Key",
    "found_at": "basement"
}
```

### DELETE - Remove Item from Inventory
```
Method: DELETE
URL: http://localhost:8887/api/dbs2/inventory
Headers: Content-Type: application/json
Body (raw JSON):
{
    "index": 0
}
```
(This removes the first item, index starts at 0)

### GET Your Scores
```
Method: GET
URL: http://localhost:8887/api/dbs2/scores
```

### PUT - Submit a Score
```
Method: PUT
URL: http://localhost:8887/api/dbs2/scores
Headers: Content-Type: application/json
Body (raw JSON):
{
    "game": "ash_trail",
    "score": 150
}
```

**Response tells you if it's a new high score:**
```json
{
    "is_high_score": true,
    "scores": {
        "ash_trail": 150,
        ...
    }
}
```

### GET Minigame Completion Status
```
Method: GET
URL: http://localhost:8887/api/dbs2/minigames
```

### PUT - Mark Minigame Complete
```
Method: PUT
URL: http://localhost:8887/api/dbs2/minigames
Headers: Content-Type: application/json
Body (raw JSON):
{
    "laundry": true
}
```

### GET Leaderboard (No Login Required!)
```
Method: GET
URL: http://localhost:8887/api/dbs2/leaderboard?limit=10
```

## 4.3 Testing Error Cases

Good testing means also checking what happens when things go wrong!

### Test: Not Logged In
1. Click `Cookies` → Delete the session cookie
2. Try `GET http://localhost:8887/api/dbs2/player`
3. **Expected:** Redirect to login page (302) or error

### Test: Invalid Data
```
Method: POST
URL: http://localhost:8887/api/dbs2/inventory
Body (raw JSON):
{
    "wrong_field": "test"
}
```
**Expected:** Error message saying "Item name required"

### Test: Invalid Index
```
Method: DELETE
URL: http://localhost:8887/api/dbs2/inventory
Body: {"index": 999}
```
**Expected:** Error "Invalid index"

---

# 5. Testing with Frontend

## 5.1 Browser Console Testing

This is the fastest way to test the JavaScript API!

### Steps:
1. Go to `http://localhost:8887/login`
2. Login as `west` / `dbs2test`
3. Go to any page that has DBS2API.js loaded (or go to `/dbs2admin`)
4. Press `F12` to open Developer Tools
5. Click the `Console` tab
6. Type these commands:

```javascript
// Check if API is loaded
DBS2API
// Should show the API object

// Get your player data
await DBS2API.getPlayer()

// Get just crypto
await DBS2API.getCrypto()

// Add 50 crypto
await DBS2API.addCrypto(50)

// Check window variable updated
window.playerCrypto

// Add an item
await DBS2API.addInventoryItem("Test Item", "console")

// View inventory
await DBS2API.getInventory()

// Submit a score
await DBS2API.submitScore("ash_trail", 200)

// Mark game complete
await DBS2API.completeMinigame("ash_trail")

// Get leaderboard
await DBS2API.getLeaderboard(5)
```

## 5.2 Check Network Tab

The Network tab shows you exactly what's being sent/received!

1. Open DevTools (`F12`)
2. Click `Network` tab
3. Run a command like `await DBS2API.addCrypto(10)`
4. Look for the `crypto` request in the list
5. Click it to see:
   - **Headers:** What was sent (including cookie!)
   - **Payload:** The JSON body you sent
   - **Response:** What the server sent back

## 5.3 Testing UI Updates

If your game page has elements with these IDs, they auto-update:
- `id="crypto"`
- `id="balance"`
- `id="money"`
- `id="playerCrypto"`

**Test it:**
1. Add this to any page: `<h1>Crypto: <span id="crypto">0</span></h1>`
2. Load the page while logged in
3. The number should show your actual crypto
4. Run `await DBS2API.addCrypto(100)` in console
5. Watch the number update automatically!

---

# 6. Using the Admin Dashboard

## Access the Dashboard

1. Login as any user
2. Go to `http://localhost:8887/dbs2admin`

## What You Can Do

### View Leaderboard
- Shows top 10 players ranked by crypto
- Gold badges for top 3
- Shows completion count (X/5 minigames)

### View All Players
- See every player's data at a glance
- Progress icons show which minigames are done:
  - 📚 = Ash Trail
  - ⛏️ = Crypto Miner
  - 🐀 = Whack-a-Rat
  - 🧺 = Laundry
  - 💻 = Infinite User

### View Player Details
1. Click `View` button on any player
2. See full breakdown:
   - All inventory items
   - All high scores
   - Exact completion status
   - Timestamps

### Edit Crypto (Admin Feature)
1. Click `Edit Crypto` on any player
2. Enter new value
3. Click Save
4. Leaderboard updates automatically!

---

# 7. Common Errors & Fixes

## Error: "Not logged in" or Redirect to Login

**Cause:** Session cookie is missing or expired

**Fixes:**
- Postman: Re-do the login request
- Browser: Go to `/login` and login again
- Check: Make sure cookies aren't blocked in browser

## Error: 404 Not Found

**Cause:** Wrong URL or server not running

**Fixes:**
- Check URL spelling exactly
- Make sure server is running (`python main.py`)
- Check the port number (8887 or your config)

## Error: 500 Internal Server Error

**Cause:** Something broke on the server

**Fixes:**
- Check your terminal - Python shows the error there!
- Common causes:
  - Database doesn't exist → delete .db file and restart
  - Missing import → check main.py imports
  - Syntax error in Python code

## Error: "No data provided" or "Item name required"

**Cause:** You sent the request without proper JSON body

**Fixes:**
- Make sure you selected `raw` and `JSON` in Postman
- Check your JSON syntax (needs double quotes!)
- Add the `Content-Type: application/json` header

## Error: CORS Error (in browser)

**Cause:** Browser blocking cross-origin request

**Fix:** This shouldn't happen if frontend and backend are same origin. If it does, you might be accessing wrong URL.

## Data Not Saving

**Causes & Fixes:**
1. Not logged in → Login first
2. Database locked → Restart server
3. Wrong method → Use PUT not GET for updates

## How to Debug Like a Pro

1. **Check Terminal:** Python errors show here
2. **Check Network Tab:** See exactly what was sent/received
3. **Check Console:** JavaScript errors show here
4. **Add print statements:** In Python, add `print(data)` to see what's happening
5. **Check Database Directly:**
   ```python
   # In Python shell
   from main import app, db
   from model.dbs2_player import DBS2Player
   with app.app_context():
       players = DBS2Player.query.all()
       for p in players:
           print(p.read())
   ```

---

# 8. AP CSP Exam Connections

This project demonstrates many AP CSP concepts! Here's how to explain them:

## Big Idea 2: Data

### 2.1 Binary/Data Representation
- JSON converts data to text format for transmission
- Database stores data in structured binary format

### 2.3 Extracting Information from Data
- Leaderboard queries database and ranks by crypto
- Admin dashboard aggregates player statistics
- High score system compares and updates records

**Example CPT Language:**
> "The program extracts information from the database by querying player records and calculating aggregate statistics like completion rates and rankings."

## Big Idea 3: Algorithms

### 3.1 Variables and Assignments
```python
# In dbs2_player.py
self._crypto = crypto  # Variable assignment
player.update({'add_crypto': 50})  # Updating stored value
```

### 3.3 Mathematical Expressions
```python
# Adding crypto uses arithmetic
self._crypto += data['add_crypto']
# Ensuring non-negative
self._crypto = max(0, value)
```

### 3.5 Boolean Expressions
```python
# Checking if all minigames complete
self._completed_all = (
    self._completed_ash_trail and
    self._completed_crypto_miner and
    self._completed_whackarat and
    self._completed_laundry and
    self._completed_infinite_user
)
```

### 3.6 Conditionals
```python
# In dbs2_api.py
if 'crypto' in data:
    player.update({'crypto': data['crypto']})
elif 'add' in data:
    player.update({'add_crypto': data['add']})
```

### 3.8 Iteration
```python
# Looping through players for leaderboard
for player in players:
    entry = player.read()
    entry['rank'] = rank
    leaderboard.append(entry)
    rank += 1
```

### 3.9 Developing Algorithms
The score system algorithm:
1. Get current scores
2. Check if new score > existing score
3. If yes, update and save
4. Return whether it was a high score

```python
def update_score(self, game_name, score):
    current = self.scores
    if game_name not in current or score > current[game_name]:
        current[game_name] = score
        self.scores = current
        db.session.commit()
        return True  # New high score!
    return False  # Not a high score
```

### 3.10 Lists
```python
# Inventory is a list
inventory = [
    {'name': 'Key', 'found_at': 'room1'},
    {'name': 'Map', 'found_at': 'room2'}
]

# Adding to list
current.append(item)

# Removing from list by index
removed = current.pop(index)
```

## Big Idea 4: Computing Systems & Networks

### 4.1 The Internet
- HTTP protocol for client-server communication
- Requests travel from browser → server → database → back

### 4.2 Fault Tolerance
```python
# Error handling prevents crashes
try:
    db.session.commit()
    return self
except:
    db.session.rollback()  # Undo failed changes
    return None
```

## Create Performance Task (CPT) Connections

If using this for CPT, you can describe:

**Input:** User actions (clicking buttons, completing minigames)

**List Usage:** 
- Inventory stores items as a list
- Can add items (append)
- Can remove items (pop by index)
- Program iterates through list to display

**Procedure with Parameter:**
```python
def update_score(self, game_name, score):  # Two parameters!
    # Algorithm with sequencing, selection, iteration
```

**Output:** 
- Updated UI showing new crypto balance
- Leaderboard showing ranked players
- Success/error messages

---

# 9. Quick Reference Cheat Sheet

## API Endpoints Summary

| Action | Method | URL | Body |
|--------|--------|-----|------|
| Get player data | GET | `/api/dbs2/player` | - |
| Get crypto | GET | `/api/dbs2/crypto` | - |
| Add crypto | PUT | `/api/dbs2/crypto` | `{"add": 50}` |
| Set crypto | PUT | `/api/dbs2/crypto` | `{"crypto": 500}` |
| Get inventory | GET | `/api/dbs2/inventory` | - |
| Add item | POST | `/api/dbs2/inventory` | `{"name": "X", "found_at": "Y"}` |
| Remove item | DELETE | `/api/dbs2/inventory` | `{"index": 0}` |
| Get scores | GET | `/api/dbs2/scores` | - |
| Submit score | PUT | `/api/dbs2/scores` | `{"game": "X", "score": 100}` |
| Get minigame status | GET | `/api/dbs2/minigames` | - |
| Complete minigame | PUT | `/api/dbs2/minigames` | `{"ash_trail": true}` |
| Get leaderboard | GET | `/api/dbs2/leaderboard?limit=10` | - |

## JavaScript Quick Reference

```javascript
// After logging in, in browser console:

// Read operations
await DBS2API.getPlayer()
await DBS2API.getCrypto()
await DBS2API.getInventory()
await DBS2API.getScores()
await DBS2API.getMinigameStatus()
await DBS2API.getLeaderboard(10)

// Write operations
await DBS2API.addCrypto(50)
await DBS2API.setCrypto(1000)
await DBS2API.addInventoryItem("Item Name", "location")
await DBS2API.removeInventoryItem(0)
await DBS2API.submitScore("game_name", 100)
await DBS2API.completeMinigame("game_name")

// Check window variables
window.playerCrypto
window.playerBalance
window.playerInventory
```

## Test Accounts

| User | Pass | Use For |
|------|------|---------|
| west | dbs2test | Full completion testing |
| cyrus | dbs2test | Partial completion |
| maya | dbs2test | Early game state |

## File Locations

```
project/
├── main.py                 # Server entry point
├── model/
│   └── dbs2_player.py     # Database model
├── api/
│   └── dbs2_api.py        # API endpoints
├── templates/
│   └── dbs2admin.html     # Admin dashboard
└── assets/js/DBS2/
    ├── DBS2API.js         # Frontend API client
    └── StatsManager.js    # Legacy wrapper
```

## Debugging Checklist

- [ ] Is the server running? (Check terminal)
- [ ] Am I logged in? (Check for session cookie)
- [ ] Is the URL correct? (Check spelling and port)
- [ ] Did I set Content-Type header for POST/PUT?
- [ ] Is my JSON valid? (Use jsonlint.com to check)
- [ ] What does the Network tab show?
- [ ] What errors are in the Console?
- [ ] What errors are in the Terminal?

---
