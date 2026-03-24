# Single Responsibility Principle (SRP) Refactoring — LaundryGame.js

This document shows how `startValidationGame()` in `LaundryGame.js` was refactored to follow the Single Responsibility Principle using the **orchestrator + helpers** pattern.

---

## The Problem

`startValidationGame()` was a single **538-line** function that handled six distinct responsibilities:

1. Game state initialisation
2. DOM creation (~250 lines of inline HTML/CSS for overlay, container, header, progress bar, wallet panel, transaction card, action buttons, tips panel, feedback overlay, results screen)
3. Event handler wiring
4. Transaction rendering with wallet highlighting and double-spend warnings
5. Decision handling and feedback display
6. Results screen with reward claiming via backend API

This violates SRP because a change to any one concern (e.g. tweaking the tips panel layout) required navigating a 538-line function and risking unintended side effects on unrelated logic.

---

## Before (538 lines, 6+ responsibilities)

```javascript
function startValidationGame(baseurl, isFirstCompletion, onComplete) {
    // 1. Game state initialisation (5 lines)
    const transactions = generateTransactions();
    let currentTxIndex = 0;
    let correctAnswers = 0;
    let totalAnswered = 0;
    let processedTxIds = new Set();
    const rewardPerCorrect = 2;

    // 2. DOM creation — overlay, container, header, progress bar,
    //    wallet panel, transaction card, action buttons, tips panel,
    //    feedback overlay, results screen (~250 lines of inline HTML/CSS)
    const overlay = document.createElement('div');
    overlay.id = 'minigame-overlay';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.85);
        ...
    `;

    const container = document.createElement('div');
    container.id = 'minigame-container';
    container.style.cssText = `
        width: 95%; max-width: 1000px; height: 90vh;
        background: linear-gradient(135deg, #0a0a15 0%, #1a1a2e 100%);
        ...
    `;

    // Header
    const header = document.createElement('div');
    header.style.cssText = `...`;
    header.innerHTML = `
        <div style="display: flex; align-items: center; gap: 15px;">
            <h1 style="...">📋 TRANSACTION VALIDATOR</h1>
            ...
        </div>
        <button id="exit-btn" style="...">EXIT</button>
    `;
    container.appendChild(header);

    // Score/Progress bar
    const progressBar = document.createElement('div');
    progressBar.style.cssText = `...`;
    progressBar.innerHTML = `
        <div id="progress-text">Transaction <span>1</span> of ${transactions.length}</div>
        <div id="score-text">Correct: <span id="correct-count">0</span>/${transactions.length}</div>
        <div id="reward-text">Earned: <span id="earned-ada">0</span> ${COIN_SYMBOL}</div>
    `;
    container.appendChild(progressBar);

    // Main game area (~120 lines)
    const gameArea = document.createElement('div');
    gameArea.style.cssText = `display: flex; gap: 20px; flex: 1; min-height: 0;`;

    // Left panel - Wallet Balances (~30 lines)
    const walletPanel = document.createElement('div');
    walletPanel.style.cssText = `width: 250px; ...`;
    walletPanel.innerHTML = `
        <h3>💰 WALLET BALANCES</h3>
        <div id="wallet-list">
            ${Object.entries(WALLETS).map(([addr, data]) => `
                <div id="wallet-${addr}" style="...">
                    <div>${data.name}</div>
                    <div>${addr}</div>
                    <div>Balance: <strong>${data.balance} ADA</strong></div>
                </div>
            `).join('')}
        </div>
    `;
    gameArea.appendChild(walletPanel);

    // Center panel - Transaction Details + Action Buttons (~40 lines)
    const txPanel = document.createElement('div');
    txPanel.style.cssText = `flex: 1; ...`;
    const txCard = document.createElement('div');
    txCard.id = 'tx-card';
    txCard.style.cssText = `...`;
    txPanel.appendChild(txCard);
    const actionBar = document.createElement('div');
    actionBar.innerHTML = `
        <button id="reject-btn" style="...">✗ REJECT</button>
        <button id="approve-btn" style="...">✓ APPROVE</button>
    `;
    txPanel.appendChild(actionBar);
    gameArea.appendChild(txPanel);

    // Right panel - Tips (~30 lines)
    const tipsPanel = document.createElement('div');
    tipsPanel.style.cssText = `width: 220px; ...`;
    tipsPanel.innerHTML = `
        <h3>💡 VALIDATION TIPS</h3>
        <div>
            <div>✓ Balance Check — Sender must have enough...</div>
            <div>✓ Signature — Must match the sender's wallet...</div>
            <div>✓ Double Spend — Check remaining balance...</div>
        </div>
    `;
    gameArea.appendChild(tipsPanel);
    container.appendChild(gameArea);

    // Feedback overlay + Results screen (~20 lines)
    const feedbackOverlay = document.createElement('div');
    feedbackOverlay.id = 'feedback-overlay';
    feedbackOverlay.style.cssText = `position: absolute; ... display: none; z-index: 100;`;
    container.appendChild(feedbackOverlay);
    const resultsScreen = document.createElement('div');
    resultsScreen.id = 'results-screen';
    resultsScreen.style.cssText = `position: absolute; ... display: none; z-index: 200;`;
    container.appendChild(resultsScreen);

    overlay.appendChild(container);
    document.body.appendChild(overlay);

    // 3. Event handler wiring
    document.getElementById('exit-btn').onclick = () => {
        window.laundryMinigameActive = false;
        window.minigameActive = false;
        document.body.removeChild(overlay);
    };
    document.getElementById('approve-btn').onclick = () => handleDecision(true);
    document.getElementById('reject-btn').onclick = () => handleDecision(false);

    displayTransaction(transactions[currentTxIndex]);

    // 4. Transaction rendering (~85 lines)
    function displayTransaction(tx) {
        const wallet = WALLETS[tx.from];
        const toWallet = WALLETS[tx.to];

        // Highlight relevant wallets
        document.querySelectorAll('[id^="wallet-"]').forEach(el => {
            el.style.borderLeftColor = '#0033ad';
            el.style.background = 'rgba(50,50,80,0.3)';
        });
        const fromWalletEl = document.getElementById(`wallet-${tx.from}`);
        const toWalletEl = document.getElementById(`wallet-${tx.to}`);
        if (fromWalletEl) {
            fromWalletEl.style.borderLeftColor = '#FF9800';
            fromWalletEl.style.background = 'rgba(255,152,0,0.15)';
        }
        if (toWalletEl) {
            toWalletEl.style.borderLeftColor = '#4CAF50';
            toWalletEl.style.background = 'rgba(76,175,80,0.15)';
        }

        // Check double-spend
        let doubleSpendWarning = '';
        if (tx.requiresPriorTx && processedTxIds.has(tx.requiresPriorTx)) {
            doubleSpendWarning = `<div style="...">⚠️ Note: You previously approved...</div>`;
        }

        txCard.innerHTML = `
            <div>📝 Transaction ${tx.id} — PENDING VALIDATION</div>
            <div style="display: grid; grid-template-columns: 1fr auto 1fr; ...">
                <!-- FROM panel --> ... <!-- Amount + Arrow --> ... <!-- TO panel --> ...
            </div>
            <div>DIGITAL SIGNATURE: ${tx.signature}</div>
            ${doubleSpendWarning}
        `;
    }

    // 5. Decision handling + feedback (~70 lines)
    function handleDecision(approved) {
        const tx = transactions[currentTxIndex];
        const isCorrect = (approved === tx.isValid);
        totalAnswered++;
        if (isCorrect) {
            correctAnswers++;
            if (approved) processedTxIds.add(tx.id);
        }
        document.getElementById('correct-count').textContent = correctAnswers;
        document.getElementById('earned-ada').textContent = correctAnswers * rewardPerCorrect;
        showFeedback(isCorrect, tx, approved);
    }

    function showFeedback(isCorrect, tx, userApproved) {
        feedbackOverlay.style.display = 'flex';
        const feedbackCard = document.createElement('div');
        feedbackCard.style.cssText = `
            background: ${isCorrect ? 'linear-gradient(...)' : 'linear-gradient(...)'};
            ...
        `;
        feedbackCard.innerHTML = `
            <div>${isCorrect ? '✓' : '✗'}</div>
            <h2>${isCorrect ? 'CORRECT!' : 'INCORRECT'}</h2>
            <p>You ${userApproved ? 'approved' : 'rejected'} this transaction...</p>
            <div>EXPLANATION: ${tx.reason}</div>
            ${isCorrect ? `<div>+${rewardPerCorrect} ${COIN_SYMBOL} earned!</div>` : ''}
            <button id="next-tx-btn">${currentTxIndex < transactions.length - 1 ? 'NEXT' : 'RESULTS'}</button>
        `;
        feedbackOverlay.innerHTML = '';
        feedbackOverlay.appendChild(feedbackCard);
        document.getElementById('next-tx-btn').onclick = () => {
            feedbackOverlay.style.display = 'none';
            currentTxIndex++;
            if (currentTxIndex < transactions.length) {
                document.getElementById('progress-text').innerHTML = `Transaction ${currentTxIndex + 1} of ...`;
                displayTransaction(transactions[currentTxIndex]);
            } else {
                showResults();
            }
        };
    }

    // 6. Results + reward claiming (~100 lines)
    async function showResults() {
        const totalReward = correctAnswers * rewardPerCorrect;
        const percentage = Math.round((correctAnswers / transactions.length) * 100);
        resultsScreen.style.display = 'flex';
        resultsScreen.innerHTML = `
            <div>
                <h1>VALIDATION COMPLETE</h1>
                <div>${percentage >= 80 ? '🏆' : percentage >= 50 ? '📋' : '📝'}</div>
                <div>ACCURACY: ${percentage}%</div>
                <div>REWARDS EARNED: ${totalReward} ${COIN_SYMBOL}</div>
                <p>${percentage >= 80 ? "Excellent work!..." : ...}</p>
                <button id="claim-reward-btn">CLAIM ${totalReward} ${COIN_SYMBOL}</button>
            </div>
        `;
        document.getElementById('claim-reward-btn').onclick = async () => {
            const btn = document.getElementById('claim-reward-btn');
            btn.textContent = 'Saving...';
            btn.disabled = true;
            try {
                await rewardMinigame(MINIGAME_NAME, totalReward);
                if (isFirstCompletion) await completeMinigame(MINIGAME_NAME);
                if (window.GameControl?.leaderboard) await window.GameControl.leaderboard.refresh();
                btn.textContent = '✅ Saved!';
                setTimeout(() => {
                    window.laundryMinigameActive = false;
                    window.minigameActive = false;
                    document.body.removeChild(overlay);
                    if (onComplete) onComplete();
                }, 800);
            } catch (error) {
                btn.textContent = '⚠️ Error - Closing...';
                setTimeout(() => {
                    window.laundryMinigameActive = false;
                    window.minigameActive = false;
                    document.body.removeChild(overlay);
                    if (onComplete) onComplete();
                }, 1500);
            }
        };
    }
}
```

---

## After (orchestrator + 11 extracted helpers)

### DOM Builder Helpers

Each function has a single job: create and return one DOM element.

```javascript
function createGameOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'minigame-overlay';
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.85);
        display: flex; justify-content: center; align-items: center;
        z-index: 10000;
    `;
    return overlay;
}

function createGameContainer() { /* → returns the styled container div */ }
function createHeader() { /* → returns header with title + exit button */ }
function createProgressBar(totalCount) { /* → returns score/progress bar */ }
function createWalletPanel() { /* → returns the left wallet-balances panel */ }
function createTransactionPanel() { /* → returns center panel with tx card + action buttons */ }
function createTipsPanel() { /* → returns the right tips panel */ }
function createHiddenOverlay(id, zIndex, bg) { /* → generic hidden overlay (feedback / results) */ }
```

### Game-Logic Helpers

Each function does one thing with data — no DOM creation mixed in.

```javascript
function highlightWallets(fromAddr, toAddr) {
    // Resets all wallet highlights, then highlights the from/to wallets
    document.querySelectorAll('[id^="wallet-"]').forEach(el => {
        el.style.borderLeftColor = '#0033ad';
        el.style.background = 'rgba(50,50,80,0.3)';
    });
    const fromEl = document.getElementById(`wallet-${fromAddr}`);
    const toEl = document.getElementById(`wallet-${toAddr}`);
    if (fromEl) { fromEl.style.borderLeftColor = '#FF9800'; ... }
    if (toEl)   { toEl.style.borderLeftColor = '#4CAF50'; ... }
}

function buildDoubleSpendWarning(tx, processedTxIds) {
    // Returns warning HTML string if double-spend detected, else ''
    if (tx.requiresPriorTx && processedTxIds.has(tx.requiresPriorTx)) {
        return `<div style="...">⚠️ Note: You previously approved...</div>`;
    }
    return '';
}

function buildTransactionCardHTML(tx) {
    // Returns the full HTML for the transaction card (from/to/amount/signature)
    ...
}

function buildFeedbackCardHTML(isCorrect, tx, userApproved, rewardPerCorrect) {
    // Returns the inner HTML for the correct/incorrect feedback card
    ...
}

function buildResultsHTML(correctAnswers, totalCount, totalReward) {
    // Returns the full results screen HTML (accuracy %, rewards, claim button)
    ...
}
```

### Backend Interaction Helpers

```javascript
async function claimRewards(totalReward, isFirstCompletion) {
    await rewardMinigame(MINIGAME_NAME, totalReward);
    if (isFirstCompletion) await completeMinigame(MINIGAME_NAME);
    if (window.GameControl?.leaderboard) {
        try { await window.GameControl.leaderboard.refresh(); } catch (e) {}
    }
}

function closeGame(overlay, onComplete) {
    window.laundryMinigameActive = false;
    window.minigameActive = false;
    document.body.removeChild(overlay);
    if (onComplete) onComplete();
}
```

### Orchestrator

The main function is now ~50 lines — it assembles DOM from builders, wires event handlers, and delegates to helpers.

```javascript
function startValidationGame(baseurl, isFirstCompletion, onComplete) {
    const transactions = generateTransactions();
    let currentTxIndex = 0;
    let correctAnswers = 0;
    let processedTxIds = new Set();
    const rewardPerCorrect = 2;

    // Assemble the DOM from builder helpers
    const overlay = createGameOverlay();
    const container = createGameContainer();
    container.appendChild(createHeader());
    container.appendChild(createProgressBar(transactions.length));

    const gameArea = document.createElement('div');
    gameArea.style.cssText = `display: flex; gap: 20px; flex: 1; min-height: 0;`;
    gameArea.appendChild(createWalletPanel());
    gameArea.appendChild(createTransactionPanel());
    gameArea.appendChild(createTipsPanel());
    container.appendChild(gameArea);

    const feedbackOverlay = createHiddenOverlay('feedback-overlay', 100, 'rgba(0,0,0,0.8)');
    const resultsScreen   = createHiddenOverlay('results-screen',   200, 'rgba(0,10,30,0.95)');
    container.appendChild(feedbackOverlay);
    container.appendChild(resultsScreen);

    overlay.appendChild(container);
    document.body.appendChild(overlay);

    // Wire event handlers
    document.getElementById('exit-btn').onclick = () => closeGame(overlay, null);
    document.getElementById('approve-btn').onclick = () => handleDecision(true);
    document.getElementById('reject-btn').onclick  = () => handleDecision(false);

    renderTransaction(transactions[currentTxIndex]);

    // ── Thin inner functions that delegate to helpers ──

    function renderTransaction(tx) {
        highlightWallets(tx.from, tx.to);
        document.getElementById('tx-card').innerHTML =
            buildTransactionCardHTML(tx) + buildDoubleSpendWarning(tx, processedTxIds);
    }

    function handleDecision(approved) {
        const tx = transactions[currentTxIndex];
        const isCorrect = (approved === tx.isValid);
        if (isCorrect) {
            correctAnswers++;
            if (approved) processedTxIds.add(tx.id);
        }
        document.getElementById('correct-count').textContent = correctAnswers;
        document.getElementById('earned-ada').textContent = correctAnswers * rewardPerCorrect;
        showFeedback(isCorrect, tx, approved);
    }

    function showFeedback(isCorrect, tx, userApproved) { /* delegates to buildFeedbackCardHTML */ }
    function advanceToNext() { /* increments index, calls renderTransaction or showResults */ }
    async function showResults() { /* delegates to buildResultsHTML + claimRewards + closeGame */ }
}
```

---

## Summary

| Metric | Before | After |
|--------|:------:|:-----:|
| `startValidationGame()` length | 538 lines | ~50 lines (orchestrator) |
| Number of responsibilities | 6 | 1 (wiring) |
| Extracted helpers | 0 | 11 |
| DOM builders | 0 | 8 (`createGameOverlay`, `createGameContainer`, `createHeader`, `createProgressBar`, `createWalletPanel`, `createTransactionPanel`, `createTipsPanel`, `createHiddenOverlay`) |
| Game-logic helpers | 0 | 5 (`highlightWallets`, `buildDoubleSpendWarning`, `buildTransactionCardHTML`, `buildFeedbackCardHTML`, `buildResultsHTML`) |
| Backend helpers | 0 | 2 (`claimRewards`, `closeGame`) |
