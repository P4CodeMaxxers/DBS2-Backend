# DBS2 Complete Testing Guide

## Overview
This guide covers **two testing approaches**:
1. **Frontend Testing** - Login through the website, test in browser console
2. **Postman Testing** - Test backend endpoints directly (verify API works independently)

---

# PART 1: FRONTEND TESTING

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Jekyll site - GitHub Pages or localhost:4100)        │
│  ├── /login page → User enters credentials                      │
│  ├── /dbs2 page → Game loads, calls DBS2API.js                 │
│  └── DBS2API.js → All API calls to backend                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP requests with JWT cookie
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND (Flask - localhost:8403 or production URL)             │
│  ├── /api/authenticate → Returns JWT token as cookie           │
│  ├── /api/dbs2/* → All game data endpoints                     │
│  └── Database → Stores player crypto, inventory, scores        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start Testing

### Step 1: Start Backend Server
```bash
cd your-backend-repo
./scripts/activate_flask.sh
# OR
python main.py
```
Backend should be running on `http://localhost:8403`

### Step 2: Start Frontend Server
```bash
cd DBS2-Frontend
bundle exec jekyll serve --port 4100
```
Frontend should be running on `http://localhost:4100`

### Step 3: Login
1. Go to `http://localhost:4100/login`
2. Enter test credentials:
   - Username: `west` (or `cyrus`, `maya`)
   - Password: `dbs2test`
3. Click Login
4. You should be redirected to the game or home page

### Step 4: Test the Game
1. Navigate to the DBS2 game page
2. Open browser DevTools (F12) → Console tab
3. Test API connection:
```javascript
// Should return your player data
await DBS2API.getPlayer()

// Should return your crypto balance
await DBS2API.getCrypto()

// Test adding crypto
await DBS2API.addCrypto(10)
```

---

## Testing Each Feature

### A. Player Data
```javascript
// Get all player info
const player = await DBS2API.getPlayer();
console.log(player);
// Expected: { uid, crypto, inventory, scores, minigames_completed, ... }
```

### B. Crypto System
```javascript
// Get current crypto
const crypto = await DBS2API.getCrypto();
console.log('Current crypto:', crypto);

// Add crypto (like when completing a minigame)
const newTotal = await DBS2API.addCrypto(50);
console.log('New total:', newTotal);
```

### C. Bitcoin Boost (Crypto Miner feature)
```javascript
// Get current Bitcoin boost multiplier
const boost = await DBS2API.getBitcoinBoost();
console.log(boost);
// Expected: { boost_multiplier: 1.25, btc_price_usd: 45000, btc_change_24h: 5.2 }

// Add crypto WITH boost applied
const result = await DBS2API.addCryptoWithBoost(10);
console.log(result);
// If BTC is up 10%, base 10 becomes 15 crypto
```

### D. Minigame Completion
```javascript
// Check which minigames are completed
const status = await DBS2API.getMinigameStatus();
console.log(status);
// Expected: { crypto_miner: false, infinite_user: true, laundry: false, ash_trail: false }

// Mark a minigame as complete
await DBS2API.completeMinigame('crypto_miner');
```

### E. Leaderboard
```javascript
// Get top 10 players (public, no login required)
const leaderboard = await DBS2API.getLeaderboard(10);
console.log(leaderboard);
```

---

## Testing Minigames

### Crypto Miner (Computer2)
1. Walk to Computer2, press E
2. Bitcoin boost displays at top
3. Press the shown key (no holding!)
4. Reach 50 progress to complete
5. Reward = (progress / 5) × Bitcoin boost multiplier
6. First completion: +25 bonus crypto

### Infinite User (Computer1)
1. Walk to Computer1, press E
2. Decrypt password (a=1, b=2, c=3... z=26)
3. Example: "9/19/8/15/23/7/18/5/5/14/" = "ishowgreen"
4. Create a new password
5. Reward: 15-24 crypto + 20 first-time bonus

### Laundry Machine
1. Walk to washing machine, press E
2. Drag parts to matching outlines
3. Load all 5 laundry items
4. Click Start
5. Reward: 20 crypto + 15 first-time bonus

### Ash Trail (Bookshelf)
1. Walk to Bookshelf, press E
2. Pick a book (harder = more reward)
3. Memorize the glowing path
4. Trace it from memory with WASD
5. Score based on accuracy (80%+ to pass)

---

## Common Issues & Fixes

### "Not logged in" or 401 Errors
**Cause:** JWT cookie missing or expired

**Fix:**
1. Go to `/login` page
2. Login again
3. Return to game

### CORS Errors
**Cause:** Frontend/backend on different origins

**Check backend has:**
```python
CORS(app, supports_credentials=True, origins=["http://localhost:4100"])
```

### DBS2API is undefined
**Cause:** Script not loaded

**Check:**
1. Browser Network tab for 404 on DBS2API.js
2. Import path is correct in your game files

### Leaderboard shows fallback data
**Cause:** No players in database yet

**Fix:** Complete a minigame to create your player record

---

## Test Accounts

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
   - Enter URL: `http://localhost:8887/login`

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

**Expected Response (200 OK):**
```json
{
    "uid": "west",
    "crypto": 100,
    "inventory": [],
    "scores": {},
    "minigames_completed": {
        "crypto_miner": false,
        "infinite_user": false,
        "laundry": false,
        "ash_trail": false
    }
}
```

### Common Errors:
| Status | Meaning | Fix |
|--------|---------|-----|
| 302 | Redirect to login | Cookie not sent - re-authenticate |
| 401 | Unauthorized | JWT expired - re-authenticate |

---

## Step 3: Test Crypto Operations

### Get Crypto Balance
```
Method: GET
URL: http://localhost:8887/api/dbs2/crypto
```

**Response:**
```json
{
    "crypto": 100
}
```

### Add Crypto
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
    "crypto": 200
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
    "crypto_miner": true
}
```

**Response:**
```json
{
    "message": "Minigame status updated",
    "minigames_completed": {
        "crypto_miner": true,
        "infinite_user": false,
        "laundry": false,
        "ash_trail": false
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

## HTTP Status Codes Explained

| Code | Name | What It Means | What To Do |
|------|------|---------------|------------|
| **200** | OK | ✅ Success! Everything worked | Nothing - you're good! |
| **201** | Created | ✅ Successfully created something new | Nothing - item was added |
| **302** | Redirect | ↪️ Server is sending you somewhere else | Usually means "go login first" |
| **400** | Bad Request | ❌ You sent data the server doesn't understand | Check your JSON format and field names |
| **401** | Unauthorized | 🔒 You're not logged in | Login first, check your cookie |
| **403** | Forbidden | 🚫 You're logged in but not allowed to do this | You might need admin permissions |
| **404** | Not Found | 🔍 That URL doesn't exist | Check spelling, check if server is running |
| **405** | Method Not Allowed | 🚷 Wrong HTTP method for this endpoint | Use GET instead of POST, or vice versa |
| **500** | Internal Server Error | 💥 Server crashed! | Check terminal for Python error message |

**Pro Tip:** If you see a 500 error, the actual error message is in your **terminal** (where you ran `python main.py`), not in Postman or the browser.

---

## Understanding Cookies (Simple Version)

**What is a cookie?**
A cookie is a small piece of text your browser stores. When you login, the server says "here's a cookie that proves you're logged in" and your browser saves it.

**How it works with our system:**

```
1. You POST to /login with username & password
         ↓
2. Server checks credentials, creates a "session" 
         ↓
3. Server sends back: "Set-Cookie: session=abc123xyz..."
         ↓
4. Browser saves this cookie
         ↓
5. Every future request, browser automatically sends: "Cookie: session=abc123xyz..."
         ↓
6. Server reads cookie, looks up session, knows it's you!
```

**Where to see your cookies:**
- **Browser:** DevTools → Application tab → Cookies → localhost
- **Postman:** Click "Cookies" link below the Send button

**Cookie problems:**
| Problem | Symptom | Fix |
|---------|---------|-----|
| No cookie | Every request redirects to login | Login again |
| Expired cookie | Was working, now redirects | Login again |
| Wrong domain | Cookie exists but API fails | Check you're on localhost:8587 |
| Cookies blocked | Never works | Check browser privacy settings |

**The `credentials: 'include'` line in JavaScript:**
```javascript
fetch(url, { credentials: 'include' })  // This tells browser to send cookies!
```
Without this, the browser won't send your login cookie, and the server won't know who you are.

---

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

## Step 7: Test Public Endpoints (No Auth Required)

### Leaderboard
```
GET http://localhost:8403/api/dbs2/leaderboard?limit=5
```

**Response:**
```json
{
    "leaderboard": [
        {
            "user_info": {"name": "west", "uid": "west"},
            "crypto": 200,
            "completed_all": false
        }
    ]
}
```

### Bitcoin Boost
```
GET http://localhost:8403/api/dbs2/bitcoin-boost
```

**Response:**
```json
{
    "boost_multiplier": 1.25,
    "btc_price_usd": 45000.50,
    "btc_change_24h": 5.2,
    "message": "Bitcoin is up! 1.25x crypto boost active!"
}
```

---

## Postman Collection Setup

### Create a Collection
1. Click "New" → "Collection"
2. Name it "DBS2 API"

### Add Requests in Order:
1. `POST /api/authenticate` - Run this FIRST
2. `GET /api/dbs2/player`
3. `GET /api/dbs2/crypto`
4. `PUT /api/dbs2/crypto` (add)
5. `GET /api/dbs2/minigames`
6. `PUT /api/dbs2/minigames`
7. `GET /api/dbs2/leaderboard`
8. `GET /api/dbs2/bitcoin-boost`

### Postman Tips:
- **Cookies are automatic**: After authenticating, Postman stores the JWT cookie
- **Check Cookies tab**: Click "Cookies" under the Send button to see stored cookies
- **Clear cookies to test auth**: Delete cookies to simulate logged-out state

---

## Debugging Checklist

### Backend Not Responding
```bash
# Check if Flask is running
curl http://localhost:8403/api/dbs2/leaderboard

# Should return JSON, not HTML or error
```

### Authentication Issues
```bash
# In Postman, after POST /api/authenticate:
# 1. Check response status is 200
# 2. Check Cookies tab shows jwt_token_flask
# 3. Try GET /api/dbs2/player immediately after
```

### CORS Issues (Frontend only)
If frontend gets CORS errors but Postman works:
```python
# Check backend has:
CORS(app, supports_credentials=True, origins=["http://localhost:4100"])
```

### Database Issues
```bash
# Reset test user's data via admin panel
# Go to: http://localhost:8403/api/dbs2/admin
# Or use Postman to set crypto to 0:
PUT /api/dbs2/crypto
{"crypto": 0}
```

---

## Complete Test Sequence

### Postman Full Test:
1. ✅ `POST /api/authenticate` → 200 + cookie set
2. ✅ `GET /api/dbs2/player` → Returns user data
3. ✅ `PUT /api/dbs2/crypto` `{"add": 100}` → Crypto increases
4. ✅ `GET /api/dbs2/crypto` → Shows new balance
5. ✅ `PUT /api/dbs2/minigames` `{"crypto_miner": true}` → Marked complete
6. ✅ `GET /api/dbs2/leaderboard` → Shows updated data
7. ✅ `GET /api/dbs2/bitcoin-boost` → Returns multiplier

### Frontend Full Test:
1. ✅ Login at `/login` page
2. ✅ Navigate to game
3. ✅ `await DBS2API.getPlayer()` in console → Returns data
4. ✅ Play Crypto Miner → Bitcoin boost visible
5. ✅ Complete minigame → Crypto awarded
6. ✅ Check leaderboard updated

---

# PART 3: HTTP Status Codes Reference

| Code | Name | What It Means | How to Fix |
|------|------|---------------|------------|
| 200 | OK | Success! | Nothing to fix |
| 201 | Created | Resource created successfully | Nothing to fix |
| 302 | Redirect | Not logged in, redirecting to login | Authenticate first |
| 400 | Bad Request | Invalid JSON or missing required fields | Check request body format |
| 401 | Unauthorized | Not logged in or token expired | Re-authenticate |
| 403 | Forbidden | Logged in but not allowed to access | Check permissions |
| 404 | Not Found | URL doesn't exist | Check endpoint URL |
| 405 | Method Not Allowed | Wrong HTTP method (GET vs POST) | Check method type |
| 500 | Internal Server Error | Python crashed | Check backend terminal for error |

---

# PART 4: How Cookies/JWT Work

```
1. POST /api/authenticate with username/password
              ↓
2. Server validates credentials
              ↓
3. Server creates JWT token
              ↓
4. Server sends "Set-Cookie: jwt_token_flask=eyJ..." header
              ↓
5. Browser/Postman stores cookie automatically
              ↓
6. All future requests include "Cookie: jwt_token_flask=eyJ..."
              ↓
7. Server reads cookie, decodes JWT, identifies user
```

### Cookie Problems:
| Problem | Symptom | Fix |
|---------|---------|-----|
| No cookie | 302 redirect or 401 | Login again |
| Expired cookie | 401 Unauthorized | Login again |
| Wrong domain | Cookie not sent | Check URL matches |
| Blocked by browser | Cookie not saved | Check browser settings |

### JavaScript Must Include:
```javascript
fetch(url, {
    credentials: 'include'  // ← This sends cookies!
})
```

---

# PART 5: Test Accounts

| Username | Password | Notes |
|----------|----------|-------|
| west | dbs2test | Test user 1 |
| cyrus | dbs2test | Test user 2 |
| maya | dbs2test | Test user 3 |

---

# PART 6: Quick Troubleshooting

### "I get HTML instead of JSON"
- **Cause:** Backend redirecting to login page
- **Fix:** Authenticate first, check cookie is set

### "CORS error in browser but Postman works"
- **Cause:** Browser enforces CORS, Postman doesn't
- **Fix:** Backend needs `CORS(app, supports_credentials=True)`

### "Cookie not being sent"
- **Cause:** Missing `credentials: 'include'`
- **Fix:** Check `fetchOptions` in config.js

### "500 Internal Server Error"
- **Cause:** Python exception on backend
- **Fix:** Check terminal running Flask for stack trace

### "DBS2API is undefined"
- **Cause:** Script not loaded
- **Fix:** Check Network tab for 404 on DBS2API.js

### "Leaderboard shows fallback data"
- **Cause:** No players exist yet or API error
- **Fix:** Play a minigame to create player record