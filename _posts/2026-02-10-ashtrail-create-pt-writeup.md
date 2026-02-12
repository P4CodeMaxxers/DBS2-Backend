# AP CSP Create Performance Task — Ash Trail Minigame & Leaderboard

## Program: Ash Trail — AMM Routing Recovery Educational Minigame

**Written Response 1: Program Design**

### 1a. Program Purpose and Function

This program is an **Ash Trail Memory** educational minigame that teaches users how Automated Market Maker (AMM) routing works in DeFi. Its purpose is to simulate optimal liquidity pool routing: the user watches an optimal path trace across a grid (representing token swap routes), memorizes it, then navigates the same path from memory using W/A/S/D or Arrow keys. The program outputs a score (0–100%) based on how closely the user followed the optimal route. Higher scores represent more efficient routing and less “slippage” — a core DeFi concept. The output includes visual feedback (path preview, player trail, score display) and a results screen with educational commentary. Completed runs are submitted to a backend via POST, stored in a database, and displayed on an Ash Trail leaderboard so users can compare their best routing efficiency across three difficulty levels (books).

### 1b. Video Demonstration Guide

The video demonstrates the following sequence:

- **Input:** The user selects a routing book (Direct Swap, Multi-Hop, or Complex Optimization), watches the optimal path preview, then uses **W/A/S/D or Arrow keys** to trace the route from memory. **Enter** finishes the run early. Mouse clicks select books and start the challenge.
- **Processing:** The program records the player path as a list of grid points, samples movement at 20 Hz, computes distance to the optimal path for each point, and calculates a proximity/coverage score.
- **Output:** Visual display of the path preview (glowing trace), the player’s path (blue line), score percentage, and a results screen with educational feedback about routing efficiency and slippage. The run is submitted to the backend; the leaderboard refreshes to show updated ranks.

---

## Written Response 2: Algorithm and Abstraction

### 2a. Algorithm with Sequencing, Selection, and Iteration

The core algorithm is the student-developed procedure **`computeScore(truePath, playerPath)`**, which compares the user’s path to the optimal path and returns a 0–100% score. It uses **sequencing**, **selection**, and **iteration** together.

**Code Snippet: `computeScore(truePath, playerPath)`**

```javascript
function computeScore(trueP, playerP) {
  if (!trueP || trueP.length === 0 || !playerP || playerP.length === 0) return 0;
  if (playerP.length < 5) return 0;

  let totalDistanceTraveled = 0;
  for (let i = 1; i < playerP.length; i++) {
    const dx = playerP[i].x - playerP[i-1].x;
    const dy = playerP[i].y - playerP[i-1].y;
    totalDistanceTraveled += Math.sqrt(dx * dx + dy * dy);
  }

  let truePathLength = 0;
  for (let i = 1; i < trueP.length; i++) {
    const dx = trueP[i].x - trueP[i-1].x;
    const dy = trueP[i].y - trueP[i-1].y;
    truePathLength += Math.sqrt(dx * dx + dy * dy);
  }

  if (totalDistanceTraveled < truePathLength * 0.1) return 0;

  const pathLengthRatio = totalDistanceTraveled / truePathLength;
  let excessPenalty = 1.0;
  if (pathLengthRatio > 2.5) {
    excessPenalty = Math.max(0.1, 1.0 - (pathLengthRatio - 2.5) * 0.3);
  } else if (pathLengthRatio > 2.0) {
    excessPenalty = Math.max(0.5, 1.0 - (pathLengthRatio - 2.0) * 0.6);
  }
  // ... proximity and coverage calculation with iteration ...
  const rawScore = 0.55 * proximityFrac + 0.45 * coverageFrac;
  const penalizedScore = rawScore * excessPenalty;
  const score = Math.round(penalizedScore * 100);
  return Math.max(0, Math.min(100, score));
}
```

- **Sequencing:** Steps execute in a fixed order. The procedure first computes total distance traveled (player path), then true path length, then path length ratio, then excess penalty, then proximity and coverage sums, then final score. Changing this order would break the logic.
- **Selection:** Multiple selection statements: (1) early returns if paths are empty or too short; (2) `if (totalDistanceTraveled < truePathLength * 0.1) return 0` to reject very short runs; (3) `if (pathLengthRatio > 2.5)` and `else if (pathLengthRatio > 2.0)` to apply different excess-penalty rules.
- **Iteration:** Several `for` loops: one iterates over `playerP` to compute total distance traveled; another over `trueP` for true path length; others over `playerP` and `trueP` (via helper `distanceToPath`) to compute proximity and coverage fractions. The helper `distanceToPath` iterates over path segments to find the minimum distance from a point to the path.

### 2b. Abstraction: Data and Procedural

**Data Abstraction: `BOOKS` List**

```javascript
const BOOKS = [
  {
    id: "defi_grimoire",
    title: "Direct Swap Route",
    difficulty: 1,
    requiredScore: 60,
    path: buildWavePath(),
    routingExample: "SOL → USDC",
    // ...
  },
  {
    id: "lost_ledger",
    title: "Multi-Hop Routing",
    difficulty: 2,
    // ...
  },
  {
    id: "proof_of_burn",
    title: "Complex Multi-Pool Optimization",
    difficulty: 3,
    // ...
  },
];
```

The `BOOKS` list stores routing scenarios. Each entry includes an id, title, difficulty, required score, path (a list of grid points), and routing example. The program uses this list to drive book selection, path display, and difficulty-based scoring. Without it, each book would need separate variables and duplicated logic.

**Data Abstraction: `playerPath` List**

The `playerPath` list stores the sequence of grid points `{x, y}` sampled during the run. It is used by `computeScore` to compare the user’s route with the optimal path and by `submitAshTrailRun` to send the trace to the backend for ghost replays. Without this list, the program could not compute routing accuracy or persist runs.

**Data Abstraction: Backend `ashtrail_runs` Table**

```python
class AshTrailRun(db.Model):
    __tablename__ = 'ashtrail_runs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.String(64), nullable=False)
    score = db.Column(db.Float, nullable=False, default=0)
    _trace = db.Column(db.Text, nullable=False, default='[]')  # JSON list of {x,y}
    guest_name = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

The backend uses a database table (a list of rows) to store runs. Each row holds user_id, book_id, score, and trace (a serialized list of points). The GET and POST endpoints read and write this list to serve the leaderboard and run submissions. Without this structure, runs could not be persisted or ranked.

**Procedural Abstraction: `computeScore(truePath, playerPath)`**

This student-developed procedure encapsulates all scoring logic. It takes two lists (optimal path and player path) and returns a 0–100 score. It is called from `finishRun()` after the user completes a run. Without this abstraction, scoring logic would be spread across multiple places and harder to maintain or change.

**Procedural Abstraction: `fetchAshTrailLeaderboard(book, limit)`**

```javascript
async fetchAshTrailLeaderboard(book = 'defi_grimoire', limit = 10) {
  const gameKey = `ash_trail_${book}`;
  const url = `${this.apiBase}/leaderboard/minigame?game=${encodeURIComponent(gameKey)}&limit=${limit}`;
  const response = await fetch(url, { method: 'GET', credentials: 'include' });
  const data = await response.json();
  const rows = data.leaderboard || [];
  // Build runLookup Map from getAshTrailRuns(book, ...)
  // Merge rows, sort by score descending, assign rank
  return allRows.map((entry, idx) => ({
    rank: entry.rank ?? idx + 1,
    name: userInfo.name || uid || 'Unknown',
    score: scoreValue,
    // ...
  }));
}
```

This procedure fetches leaderboard data from the API and merges it with Ash Trail runs. It uses a list (`rows`), sorts entries by score, and assigns ranks. It contributes to the program by centralizing leaderboard fetching and formatting so the Ash Trail tab can display ranked players consistently.

---

## Written Response 3: Skill B — Individual

### 3a. Program Purpose and Function

This program is an Ash Trail Memory minigame that teaches AMM routing in DeFi. The user selects a routing book, watches an optimal path trace (representing token swap routes), memorizes it, then traces the path from memory using W/A/S/D or Arrow keys. The program outputs a 0–100% score (visual and textual), educational feedback about slippage, and submits the run to a backend. Completed runs appear on the Ash Trail leaderboard, where users compare routing efficiency across books. Output includes the path preview, player trail, score display, results screen, and leaderboard.

### 3b. Data Abstraction

**Frontend: `BOOKS` List**

```javascript
const BOOKS = [
  { id: "defi_grimoire", title: "Direct Swap Route", difficulty: 1, path: buildWavePath(), ... },
  { id: "lost_ledger", title: "Multi-Hop Routing", difficulty: 2, path: buildCrossPath(), ... },
  { id: "proof_of_burn", title: "Complex Multi-Pool Optimization", difficulty: 3, path: buildHeartPath(), ... },
];
```

The `BOOKS` list stores routing scenarios. It is accessed by the book selection scene and by `computeScore` for difficulty-based parameters. Without this list, each scenario would require separate variables and duplicated logic.

**Backend: `ashtrail_runs` as a List of Records**

The backend stores runs in the `ashtrail_runs` table. Each row has `id`, `user_id`, `book_id`, `score`, `_trace` (JSON list of `{x,y}`), and `created_at`. The GET endpoint returns `runs` (a list of run records). The POST endpoint accepts `book_id`, `score`, and `trace` and adds a new row. Without this list structure, runs could not be stored or retrieved for the leaderboard.

### 3c. Managing Complexity

**Frontend: `runLookup` Map and `allRows` List**

```javascript
const runLookup = new Map();
runPayload.runs.forEach((run) => {
  const key = (uid === '_ashtrail_guest') ? `guest:${name}` : (uid || '');
  const existing = runLookup.get(key);
  if (!existing || (Number(run.score) || 0) > (Number(existing.score) || 0)) {
    runLookup.set(key, run);
  }
});
const allRows = [...rows];
allRows.sort((a, b) => (Number(b.score) || 0) - (Number(a.score) || 0));
return allRows.map((entry, idx) => ({ ...entry, rank: entry.rank ?? idx + 1 }));
```

The leaderboard uses a `Map` (`runLookup`) to keep the best run per user and a list (`allRows`) to merge API leaderboard entries with guest runs, sort by score descending, and assign ranks. Without these structures, the logic for combining minigame scores and Ash Trail runs would be scattered and harder to maintain.

### 3d. Procedural Abstraction

**`computeScore(truePath, playerPath)`**

The student-developed procedure `computeScore(truePath, playerPath)` encapsulates routing accuracy scoring. It takes the optimal path and the player path (both lists of grid points), computes distance traveled, path length ratio, excess penalty, proximity and coverage fractions, and returns a 0–100 score. It contributes to the program by centralizing scoring logic so `finishRun()` only needs a single call.

**Called from:**

```javascript
async function finishRun() {
  const score = computeScore(truePath, playerPath);
  // ...
  const result = await submitAshTrailRun(currentBook.id, score, trace);
  renderResultsScene(score);
}
```

### 3e. Algorithm Implementation

Inside `computeScore()`, the algorithm uses:

- **Sequencing:** Compute total distance traveled, then true path length, then path length ratio, then excess penalty, then proximity/coverage sums, then final score. Order matters.
- **Selection:** Early returns for invalid paths; `if (pathLengthRatio > 2.5)` and `else if (pathLengthRatio > 2.0)` to apply different penalties; conditional logic inside `weightFromDist` and score clamping.
- **Iteration:** `for` loops over `playerP` to compute distance traveled; over `trueP` for path length; over `playerP` and `trueP` in `distanceToPath` and coverage calculations. The helper `distanceToPath` iterates over path segments to find the minimum distance from a point to the path.

---

## Skill B — Frontend, Backend, POST Request

### Frontend for Input/Output

- **Input:** User actions (keyboard: W/A/S/D, Arrow keys, Enter; mouse: book selection, Start buttons). These trigger events that update `pressedDirs`, `playerPath`, and call `finishRun()`.
- **Output:** Visual output on an HTML5 canvas (path preview, player trail, score) and textual/visual output in the results scene and leaderboard panel.

### Backend Using a List / Data Structure

- The backend uses the `ashtrail_runs` table (a list of rows) to store runs. Each row has `user_id`, `book_id`, `score`, `_trace` (JSON list of points).
- The minigame leaderboard endpoint (`GET /api/dbs2/leaderboard/minigame?game=ash_trail_<book>`) reads player scores from `DBS2Player.scores`, builds a list of entries, sorts by score descending, and returns ranked data.
- The Ash Trail runs endpoint (`GET /api/dbs2/ash-trail/runs?book_id=...`) returns a list of runs ordered by score descending. No hard-coded leaderboard; all data comes from the database.

### POST Request Includes Both Input and Output

- **POST `/api/dbs2/ash-trail/runs`** — **Input:** `book_id`, `score`, `trace` (list of `{x,y}`), and optionally `guest_name`. **Output:** JSON response with `{ success: true, run: { id, user_info, book_id, score, created_at, trace } }`.
- The frontend calls `submitAshTrailRun(bookId, score, trace)`, which sends a POST with the user’s run data and receives the stored run (including id) as output. This follows the requirement that a POST includes both input and output.

---

## Requirement Checklist (Component A)

| Requirement | Implementation |
|-------------|----------------|
| **Input** from user (actions that trigger events) | W/A/S/D, Arrow keys, Enter, mouse clicks for book selection and Start |
| **List or collection type** | `BOOKS`, `playerPath`, `truePath`, `runLookup` Map, `allRows`, backend `ashtrail_runs` table |
| **Procedure** with name, return type, parameters | `computeScore(truePath, playerPath)` — returns number; `fetchAshTrailLeaderboard(book, limit)` — returns Promise of list |
| **Algorithm** with sequencing, selection, iteration | `computeScore` — order of steps; if/else for penalty and early returns; for loops over paths |
| **Calls** to student-developed procedure | `finishRun()` calls `computeScore(truePath, playerPath)`; Leaderboard calls `fetchAshTrailLeaderboard()` |
| **Output** (visual, textual) based on input | Canvas path, trail, score; results screen; leaderboard display |  
