# Single Responsibility Principle (SRP) Refactoring — Before & After

This document shows the functions that were refactored across both the **DBS2-Backend** and **DBS2-Frontend** repositories to follow the Single Responsibility Principle using the **orchestrator + helpers** pattern.

---

## Backend — `model/user.py` → `User.update()`

### Before (80 lines, 4+ responsibilities)

```python
def update(self, inputs):
    if not isinstance(inputs, dict):
        return self

    name = inputs.get("name", "")
    uid = inputs.get("uid", "")
    email = inputs.get("email", "")
    sid = inputs.get("sid", "")
    password = inputs.get("password", "")
    pfp = inputs.get("pfp", None)
    kasm_server_needed = inputs.get("kasm_server_needed", None)
    grade_data = inputs.get("grade_data", None)
    ap_exam = inputs.get("ap_exam", None)
    class_list = inputs.get("class", None) or inputs.get("_class", None)
    school = inputs.get("school", None)
    old_uid = self.uid
    old_kasm_server_needed = self.kasm_server_needed

    if name:
        self.name = name
    if uid:
        self.set_uid(uid)
    if email:
        self.email = email
    # ... 15 more field updates ...
    if school is not None:
        self.school = school

    if not email:
        if email == "?":
            self.set_email()

    try:
        kasm_user = KasmUser()
        if self.kasm_server_needed:
            if old_uid != self.uid:
                kasm_user.delete(old_uid)
            kasm_user.post(self.name, self.uid, password if password else ...)
            if not old_kasm_server_needed:
                kasm_user.post_groups(self.uid, [...])
        elif old_kasm_server_needed:
            kasm_user.delete(self.uid)
    except Exception as e:
        print(f"Kasm API error for user {self.uid}: {e}")

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None
    return self
```

**Violations:** Field extraction + field application + Kasm API sync + DB commit all in one function.

### After (orchestrator + 3 helpers)

```python
def _apply_field_updates(self, inputs):
    """Apply simple field updates from inputs dict."""
    # Each field update in one place
    ...

def _sync_kasm_state(self, old_uid, old_kasm_server_needed, password):
    """Synchronise the user's Kasm server account after field updates."""
    ...

def _commit_update(self):
    """Commit the current session; rollback on integrity error."""
    ...

def update(self, inputs):                          # ← orchestrator
    if not isinstance(inputs, dict):
        return self
    old_uid = self.uid
    old_kasm_server_needed = self.kasm_server_needed
    password = self._apply_field_updates(inputs)
    self._sync_kasm_state(old_uid, old_kasm_server_needed, password)
    return self._commit_update()
```

---

## Backend — `api/user.py` → `_Security.post()` (Login)

### Before (90 lines, 4+ responsibilities)

```python
def post(self):
    try:
        body = request.get_json()
        if not body:
            return {"message": "Please provide user details", ...}, 400
        uid = body.get('uid')
        if uid is None:
            return {'message': 'User ID is missing'}, 401
        password = body.get('password')
        if not password:
            return {'message': 'Password is missing'}, 401

        user = User.query.filter_by(_uid=uid).first()
        if user is None or not user.is_password(password):
            return {'message': "Invalid user id or password"}, 401

        if user:
            try:
                token = jwt.encode({"_uid": user._uid, "exp": ...}, ...)
                is_production = not (request.host.startswith('localhost') ...)
                response_data = {
                    "message": f"Authentication for {user._uid} successful",
                    "token": token,
                    "user": {"uid": user._uid, "name": user.name, ...}
                }
                resp = jsonify(response_data)

                if is_production:
                    resp.set_cookie(..., secure=True, samesite='None')
                else:
                    resp.set_cookie(..., secure=False, samesite='Lax')
                return resp
            except Exception as e:
                return {"error": "Something went wrong", ...}, 500
        return {"message": "Error fetching auth token!", ...}, 404
    except Exception as e:
        return {"message": "Something went wrong!", ...}, 500
```

**Violations:** Request validation + user lookup/auth + JWT generation + cookie configuration + response building all in one deeply nested function.

### After (orchestrator + 4 static helpers)

```python
@staticmethod
def _validate_login_request(body):
    """Extract and validate uid/password."""
    ...

@staticmethod
def _authenticate_user(uid, password):
    """Look up the user and verify credentials."""
    ...

@staticmethod
def _generate_token(user):
    """Create a signed JWT for the given user."""
    ...

@staticmethod
def _build_auth_response(user, token):
    """Build a JSON response with the token set as a cookie."""
    ...

def post(self):                                     # ← orchestrator
    try:
        uid, password = self._validate_login_request(request.get_json())
        user = self._authenticate_user(uid, password)
        token = self._generate_token(user)
        return self._build_auth_response(user, token)
    except ValueError as ve:
        return {"message": str(ve)}, 401
    except Exception as e:
        return {"message": "Something went wrong!", "error": str(e)}, 500
```

---

## Backend — `api/user.py` → `_CRUD.post()` (User Creation)

### Before (80 lines, 3+ responsibilities)

```python
def post(self):
    body = request.get_json()
    name = body.get('name')
    if name is None or len(name) < 2:
        return {'message': 'Name is missing...'}, 400
    uid = body.get('uid')
    if uid is None or len(uid) < 2:
        return {'message': 'User ID is missing...'}, 400
    password = body.get('password')
    if password is not None:
        if len(password) < 8 and not password.startswith("pbkdf2:sha256:"):
            return {'message': 'Password must be at least 8 characters'}, 400
        user_obj = User(name=name, uid=uid, password=password)
    else:
        user_obj = User(name=name, uid=uid)

    cleaned_body = {'name': name, 'uid': uid, 'password': password, 'email': body.get('email')}
    if body.get('sid'):
        cleaned_body['sid'] = body.get('sid')
    if body.get('school'):
        cleaned_body['school'] = body.get('school')
    # ... more optional fields ...
    cleaned_body = {k: v for k, v in cleaned_body.items() if v is not None}

    try:
        user = user_obj.create(cleaned_body)
        if not user:
            db_user = User.query.filter_by(_uid=uid).first()
            if db_user:
                return jsonify(db_user.read())
            else:
                return {'message': f'Processed {name}...'}, 400
        return jsonify(user.read())
    except Exception as e:
        return {'message': f'Error creating user: {str(e)}'}, 500
```

**Violations:** Input validation + body sanitisation + user creation/persistence + error recovery all mixed together.

### After (orchestrator + 3 static helpers)

```python
@staticmethod
def _validate_user_input(body):
    """Validate required fields. Returns (name, uid, password) or raises ValueError."""
    ...

@staticmethod
def _clean_request_body(body, name, uid, password):
    """Build a dict of only the fields the User model expects."""
    ...

@staticmethod
def _create_and_persist_user(name, uid, password, cleaned_body):
    """Instantiate a User, persist it, and return the created record."""
    ...

def post(self):                                     # ← orchestrator
    body = request.get_json()
    try:
        name, uid, password = self._validate_user_input(body)
        cleaned_body = self._clean_request_body(body, name, uid, password)
        user = self._create_and_persist_user(name, uid, password, cleaned_body)
        return jsonify(user.read())
    except ValueError as ve:
        return {'message': str(ve)}, 400
    except Exception as e:
        return {'message': f'Error creating user: {str(e)}'}, 500
```

---

## Frontend — `LaundryGame.js` → `startValidationGame()`

### Before (538 lines, 6+ responsibilities)

```javascript
function startValidationGame(baseurl, isFirstCompletion, onComplete) {
    // 1. Game state initialisation (5 lines)
    const transactions = generateTransactions();
    let currentTxIndex = 0;
    let correctAnswers = 0;
    ...

    // 2. DOM creation — overlay, container, header, progress bar,
    //    wallet panel, transaction card, action buttons, tips panel,
    //    feedback overlay, results screen (~250 lines of inline HTML/CSS)
    const overlay = document.createElement('div');
    overlay.style.cssText = `position: fixed; ...`;
    const container = document.createElement('div');
    ...

    // 3. Event handler wiring (5 lines)
    document.getElementById('exit-btn').onclick = () => { ... };

    // 4. Transaction rendering logic — displayTransaction() (~85 lines)
    function displayTransaction(tx) {
        // wallet highlighting + double-spend warning + HTML template
        ...
    }

    // 5. Decision handling — handleDecision() + showFeedback() (~70 lines)
    function handleDecision(approved) { ... }
    function showFeedback(isCorrect, tx, userApproved) { ... }

    // 6. Results + reward claiming — showResults() (~100 lines)
    async function showResults() {
        // results HTML + claim button + API calls + cleanup
        ...
    }
}
```

**Violations:** DOM construction + game state + rendering + decision logic + feedback UI + results/rewards all in one 538-line function.

### After (orchestrator + 11 extracted helpers)

```javascript
// DOM builders (each returns a single DOM element)
function createGameOverlay() { ... }
function createGameContainer() { ... }
function createHeader() { ... }
function createProgressBar(totalCount) { ... }
function createWalletPanel() { ... }
function createTransactionPanel() { ... }
function createTipsPanel() { ... }
function createHiddenOverlay(id, zIndex, bg) { ... }

// Game-logic helpers (pure data → HTML)
function highlightWallets(fromAddr, toAddr) { ... }
function buildDoubleSpendWarning(tx, processedTxIds) { ... }
function buildTransactionCardHTML(tx) { ... }
function buildFeedbackCardHTML(isCorrect, tx, userApproved, rewardPerCorrect) { ... }
function buildResultsHTML(correctAnswers, totalCount, totalReward) { ... }

// Backend interaction
async function claimRewards(totalReward, isFirstCompletion) { ... }
function closeGame(overlay, onComplete) { ... }

// Orchestrator — wires everything together
function startValidationGame(baseurl, isFirstCompletion, onComplete) {
    const transactions = generateTransactions();
    let currentTxIndex = 0;
    let correctAnswers = 0;
    let processedTxIds = new Set();
    const rewardPerCorrect = 2;

    const overlay = createGameOverlay();
    const container = createGameContainer();
    container.appendChild(createHeader());
    container.appendChild(createProgressBar(transactions.length));
    // ... assemble game area from helpers ...
    document.body.appendChild(overlay);

    // Wire handlers → thin inner functions that call helpers
    document.getElementById('approve-btn').onclick = () => handleDecision(true);
    ...
}
```

---

## Frontend — `Npc.js` → `handleKeyDown()`

### Before (78 lines, 3+ responsibilities)

```javascript
handleKeyDown({ key }) {
    switch (key) {
        case 'e':
            try {
                // 1. Collision detection
                const players = GameEnv.gameObjects.filter(
                    obj => obj.state?.collisionEvents?.includes(this.spriteData.id)
                );

                if (players.length === 0) {
                    // 2. Proximity fallback for Cards NPC
                    const player = GameEnv.gameObjects.find(...);
                    if (player && this.spriteData.id === 'Cards') {
                        const dist = Math.sqrt(...);
                        if (dist < 200) {
                            this.launchCryptoChecker();
                            return;
                        }
                    }
                    return;
                }

                this.closeAllDialogues();

                // 3. NPC dispatch (large switch statement)
                switch (npcId) {
                    case 'Bookshelf':  showAshTrailMinigame(); return;
                    case 'Computer1':  infiniteUserMinigame(); return;
                    case 'Computer2':  cryptoMinerMinigame(); return;
                    case 'laundry':    showLaundryMinigame(); return;
                    case 'Cards':      this.launchCryptoChecker(); return;
                    case 'IShowGreen': Prompt.openPromptPanel(this); return;
                    case 'Closet':     showClosetShop(); return;
                    default:           Prompt.openPromptPanel(this); return;
                }
            } catch (err) { ... }
            break;
    }
}
```

**Violations:** Collision detection + proximity calculation + NPC-to-minigame dispatch all in one function with a nested switch.

### After (orchestrator + 3 helpers)

```javascript
findCollidingPlayers() {
    return GameEnv.gameObjects.filter(
        obj => obj.state?.collisionEvents?.includes(this.spriteData.id)
    );
}

isPlayerInProximity(maxDist = 200) {
    const player = GameEnv.gameObjects.find(obj => obj.spriteData?.id === 'player');
    if (!player) return false;
    const dist = Math.sqrt(...);
    return dist < maxDist;
}

dispatchNpcInteraction(npcId) {
    const minigameMap = {
        'Bookshelf':  () => showAshTrailMinigame(),
        'Computer1':  () => infiniteUserMinigame(),
        'Computer2':  () => cryptoMinerMinigame(),
        'laundry':    () => showLaundryMinigame(),
        'Cards':      () => this.launchCryptoChecker(),
        'Closet':     () => showClosetShop(),
    };
    const action = minigameMap[npcId];
    action ? action() : Prompt.openPromptPanel(this);
}

handleKeyDown({ key }) {                           // ← orchestrator
    if (key !== 'e') return;
    try {
        const players = this.findCollidingPlayers();
        if (players.length === 0) {
            if (this.spriteData.id === 'Cards' && this.isPlayerInProximity())
                this.launchCryptoChecker();
            return;
        }
        this.closeAllDialogues();
        this.dispatchNpcInteraction(this.spriteData.id);
    } catch (err) { ... }
}
```

---

## Frontend — `ClosetShop.js` → `renderShopItems()` + `handlePurchase()`

### Before — `renderShopItems()` (86 lines)

```javascript
function renderShopItems(category = 'all') {
    const baseurl = ...;
    const items = Object.values(SHOP_ITEMS);
    const filteredItems = category === 'all' ? items : items.filter(...);

    for (const item of filteredItems) {
        const price = item.price;
        const coinInfo = getCoinInfo(price.coin);
        const balance = currentWallet[price.coin] || 0;
        const canAfford = balance >= price.amount;
        // ... 60+ lines of inline HTML template with affordability logic ...
        html += `<div class="shop-item-card" ...> ... </div>`;
    }
    return html;
}
```

### After — `renderShopItems()` (orchestrator + 2 helpers)

```javascript
function filterItemsByCategory(category) {
    const items = Object.values(SHOP_ITEMS);
    return category === 'all' ? items : items.filter(item => item.category === category);
}

function buildItemCardHTML(item, baseurl) {
    // All affordability checks + HTML for a single item card
    ...
}

function renderShopItems(category = 'all') {         // ← orchestrator
    const baseurl = ...;
    const filteredItems = filterItemsByCategory(category);
    if (filteredItems.length === 0) return '<div ...>No items</div>';
    return filteredItems.map(item => buildItemCardHTML(item, baseurl)).join('');
}
```

### Before — `handlePurchase()` (62 lines)

```javascript
async function handlePurchase(itemId) {
    const item = SHOP_ITEMS[itemId];
    const balance = currentWallet[item.price.coin] || 0;
    if (balance < item.price.amount) { showMessage(...); return; }

    const btn = document.querySelector(`.shop-purchase-btn[data-item-id="${itemId}"]`);
    btn.disabled = true; btn.textContent = 'PURCHASING...'; btn.style.background = '#666';

    try {
        const result = await purchaseShopItem(itemId, item);
        if (result.success) {
            showMessage(item.unlockMessage, 'success');
            const walletData = await getWallet();
            currentWallet = walletData.raw_balances || walletData.wallet || {};
            // ... re-render grid, refresh wallet display, refresh inventory ...
        } else {
            showMessage(result.error || 'Purchase failed!', 'error');
            btn.disabled = false; btn.textContent = 'PURCHASE'; ...
        }
    } catch (e) {
        showMessage('Purchase failed!', 'error');
        btn.disabled = false; btn.textContent = 'PURCHASE'; ...
    }
}
```

### After — `handlePurchase()` (orchestrator + 4 helpers)

```javascript
function validatePurchase(item) { ... }
function disablePurchaseButton(btn) { ... }
function resetPurchaseButton(btn, coinType) { ... }
async function refreshShopAfterPurchase() { ... }

async function handlePurchase(itemId) {              // ← orchestrator
    const item = SHOP_ITEMS[itemId];
    if (!item) return;
    if (!validatePurchase(item)) { showMessage(...); return; }
    const btn = document.querySelector(...);
    disablePurchaseButton(btn);
    try {
        const result = await purchaseShopItem(itemId, item);
        if (result.success) {
            showMessage(item.unlockMessage, 'success');
            await refreshShopAfterPurchase();
        } else {
            showMessage(result.error || 'Purchase failed!', 'error');
            resetPurchaseButton(btn, item.price.coin);
        }
    } catch (e) {
        showMessage('Purchase failed!', 'error');
        resetPurchaseButton(btn, item.price.coin);
    }
}
```

---

## Summary Table

| File | Function | Before (lines) | After | Helpers Extracted |
|------|----------|:-:|:-:|:-:|
| `model/user.py` | `User.update()` | 80 | 8 (orchestrator) | 3 (`_apply_field_updates`, `_sync_kasm_state`, `_commit_update`) |
| `api/user.py` | `_Security.post()` | 90 | 8 (orchestrator) | 4 (`_validate_login_request`, `_authenticate_user`, `_generate_token`, `_build_auth_response`) |
| `api/user.py` | `_CRUD.post()` | 80 | 10 (orchestrator) | 3 (`_validate_user_input`, `_clean_request_body`, `_create_and_persist_user`) |
| `LaundryGame.js` | `startValidationGame()` | 538 | 30 (orchestrator) | 11 (DOM builders + game-logic helpers) |
| `Npc.js` | `handleKeyDown()` | 78 | 14 (orchestrator) | 3 (`findCollidingPlayers`, `isPlayerInProximity`, `dispatchNpcInteraction`) |
| `ClosetShop.js` | `renderShopItems()` | 86 | 6 (orchestrator) | 2 (`filterItemsByCategory`, `buildItemCardHTML`) |
| `ClosetShop.js` | `handlePurchase()` | 62 | 15 (orchestrator) | 4 (`validatePurchase`, `disablePurchaseButton`, `resetPurchaseButton`, `refreshShopAfterPurchase`) |
