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

## Troubleshooting 500 Errors (Player / Leaderboard / Admin)

If you see **500 (INTERNAL SERVER ERROR)** on `/api/dbs2/player`, `/api/dbs2/leaderboard`, `/api/dbs2/admin/stats`, or `/api/dbs2/admin/players`:

1. **See the actual error message (browser)**  
   - Open DevTools → **Network** tab.  
   - Click the failed request (e.g. `player`, `leaderboard?limit=10`, `admin/stats`, `admin/players`).  
   - Open the **Response** (or **Preview**) tab.  
   The backend returns JSON like `{"error": "Internal Server Error", "message": "..."}` — that `message` is the real cause (e.g. missing table, missing column). With `FLASK_DEBUG=1` you also get a `traceback` field.

2. **See the Python traceback (backend)**  
   - In the terminal where you ran `python main.py` (or your Flask command), look for the full traceback when the 500 happens.  
   - Admin/leaderboard handlers log with `traceback.print_exc()` so the last line (e.g. `OperationalError: no such column`) tells you what broke.

3. **Ensure DB tables exist**  
   - Restart the backend so `db.create_all()` runs at startup (in `main.py`).  
   - Or run: `flask custom generate_data` to create tables and test data.  
   - If the DB file was created by an older schema, delete `instance/volumes/user_management.db` (or your DB path) and restart so tables are recreated with the current schema.

4. **Admin panel “Error loading”**  
   - The admin page at `/dbs2admin` calls `/api/dbs2/admin/stats`, `/api/dbs2/leaderboard`, `/api/dbs2/leaderboard/minigame`, and `/api/dbs2/admin/players`.  
   - These endpoints are written to return **200 with empty data** on DB errors (so the UI shows “No players yet” instead of “Error loading”). If you still see 500, an unhandled exception is occurring; use steps 1–2 to read the `message` and backend traceback.

5. **Code to fix**  
   - **Player/leaderboard 500:** `api/dbs2_api.py` (player resource, leaderboard resource, `get_current_player()`).  
   - **Model/DB errors:** `model/dbs2_player.py` (e.g. `read()`, `get_or_create()`, `get_leaderboard()`).

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

| Username | Password |
|----------|----------|
| west | dbs2test |
| cyrus | dbs2test |
| maya | dbs2test |

---

## Backend Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/authenticate` | No | Login |
| GET | `/api/dbs2/player` | Yes | Get player |
| PUT | `/api/dbs2/crypto` | Yes | Add/set crypto |
| GET | `/api/dbs2/minigames` | Yes | Completion status |
| PUT | `/api/dbs2/minigames` | Yes | Mark complete |
| GET | `/api/dbs2/leaderboard` | No | Top players |
| GET | `/api/dbs2/bitcoin-boost` | No | BTC multiplier |

---

## Verification Checklist

- [ ] Backend running on port 8403
- [ ] Frontend running on port 4100  
- [ ] Can login at /login page
- [ ] `await DBS2API.getPlayer()` returns data
- [ ] Minigames award crypto on completion
- [ ] Leaderboard refreshes with real data
- [ ] Bitcoin boost shows in Crypto Miner

---

# PART 2: POSTMAN TESTING (Backend Verification)

Use Postman to test backend endpoints **independently** of the frontend. This verifies the API works correctly.

## Postman Setup

### Base URL
```
http://localhost:8403
```

### Required Headers (for all requests)
| Key | Value |
|-----|-------|
| Content-Type | application/json |

---

## Step 1: Authenticate (Get JWT Token)

**Request:**
```
POST http://localhost:8403/api/authenticate
```

**Body (raw JSON):**
```json
{
    "uid": "west",
    "password": "dbs2test"
}
```

**Expected Response (200 OK):**
```json
{
    "message": "Authentication successful"
}
```

**IMPORTANT:** Look at the response **Cookies** tab in Postman. You should see a cookie like:
```
jwt_token_flask=eyJhbGciOiJIUzI1NiIs...
```

Postman automatically saves this cookie and sends it with future requests to the same domain.

### Common Errors:
| Status | Meaning | Fix |
|--------|---------|-----|
| 401 | Wrong password | Check password is `dbs2test` |
| 404 | User not found | Check username exists |
| 500 | Server error | Check backend terminal for Python errors |

---

## Step 2: Test Player Endpoint

**Request:**
```
GET http://localhost:8403/api/dbs2/player
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
GET http://localhost:8403/api/dbs2/crypto
```

**Response:**
```json
{
    "crypto": 100
}
```

### Add Crypto
```
PUT http://localhost:8403/api/dbs2/crypto
```

**Body:**
```json
{
    "add": 50
}
```

**Response:**
```json
{
    "crypto": 150,
    "message": "Added 50 crypto"
}
```

### Set Crypto to Specific Amount
```
PUT http://localhost:8403/api/dbs2/crypto
```

**Body:**
```json
{
    "crypto": 200
}
```

**Response:**
```json
{
    "crypto": 200,
    "message": "Crypto set to 200"
}
```

---

## Step 4: Test Minigame Completion

### Get Minigame Status
```
GET http://localhost:8403/api/dbs2/minigames
```

**Response:**
```json
{
    "crypto_miner": false,
    "infinite_user": false,
    "laundry": false,
    "ash_trail": false,
    "completed_count": 0,
    "total_minigames": 4
}
```

### Mark Minigame Complete
```
PUT http://localhost:8403/api/dbs2/minigames
```

**Body:**
```json
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

---

## Step 5: Test Inventory

### Get Inventory
```
GET http://localhost:8403/api/dbs2/inventory
```

**Response:**
```json
{
    "inventory": []
}
```

### Add Item
```
POST http://localhost:8403/api/dbs2/inventory
```

**Body:**
```json
{
    "name": "Golden Key",
    "found_at": "basement_chest"
}
```

**Response:**
```json
{
    "message": "Item added",
    "inventory": [
        {"name": "Golden Key", "found_at": "basement_chest"}
    ]
}
```

### Remove Item
```
DELETE http://localhost:8403/api/dbs2/inventory
```

**Body:**
```json
{
    "index": 0
}
```

---

## Step 6: Test Scores

### Get Scores
```
GET http://localhost:8403/api/dbs2/scores
```

**Response:**
```json
{
    "scores": {}
}
```

### Submit Score
```
PUT http://localhost:8403/api/dbs2/scores
```

**Body:**
```json
{
    "game": "crypto_miner",
    "score": 150
}
```

**Response:**
```json
{
    "message": "Score updated",
    "game": "crypto_miner",
    "score": 150,
    "is_high_score": true
}
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