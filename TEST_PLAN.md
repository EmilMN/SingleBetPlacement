# Test Plan: Single Bet Placement

**Environment:** https://qae-assignment-tau.vercel.app, latest Chrome, user `candidate-CPkDP9YYtK7Q`

**Approach:** Prioritised by risk: *what does it cost if this is wrong?* Money (balance, stake, payout) ranks above presentation. Server-side rules rank above UI-only checks, because the UI can be bypassed.

**Out of scope (spec §1):** live betting, multi-bets, other sports and mobile UX. Their in-scope counterparts are covered: pre-match only (BUG-10), one selection at a time (Test-Case-05), football only, and desktop Chrome.

| ID | Title | Priority | Type |
|---|---|---|---|
| Test-Case-01 | Place a valid bet; receipt and balance are consistent | Critical | Happy path |
| Test-Case-02 | Stake above the balance is rejected, including after consecutive bets | Critical | Negative |
| Test-Case-03 | Stake limits and format are enforced by the API | Critical | Boundary |
| Test-Case-04 | Failed placement shows the error modal; Rebet and Close work | High | Negative |
| Test-Case-05 | Bet slip replaces selections and calculates the payout | Medium | Functional |
| Test-Case-06 | API rejects bad, unauthorised and unsupported requests | Medium | Negative |

Test-Case-01 to Test-Case-03 were executed; results are in [BUG_REPORTS.md](BUG_REPORTS.md).

---

### Test-Case-01: Place a valid bet; receipt and balance are consistent

**Priority:** Critical

**Risk Rationale:** This is the core revenue journey. The receipt is the customer's record of the bet, so any mismatch leads to disputes and loss of trust. It also checks that the stake is deducted everywhere the balance is shown.

**Preconditions:** Reset the balance via the API.

**Steps:**
1. Open the app and note the header balance.
2. On an upcoming match, e.g. *Tottenham vs Liverpool*, click `1` (home, 2.75).
3. Enter stake `10`.
4. Click **Place Bet**.
5. Check the receipt.
6. Close the receipt.
7. Check the balance in the header and via `GET /api/balance`.

**Expected Result:**
- The slip shows payout €27.50, and the button shows `Placing...` while the bet is sent.
- The receipt shows a Bet ID, *Tottenham vs Liverpool*, selection Home, €10.00, odds 2.75, payout €27.50 and a timestamp.
- After closing, the slip is empty and the header and API balances are both €10.00 lower.

### Test-Case-02: Stake above the balance is rejected, including after consecutive bets

**Priority:** Critical

**Risk Rationale:** A stake above the balance means betting money the customer doesn't have. That is a direct financial loss and a responsible-gambling failure. The server must enforce this rule, because the UI check can be bypassed or stale.

**Steps:**
1. Reset the balance (€120) and bet €100 + €14.01 via the API to reach €5.99. Reload.
2. Enter stake `10`.
3. Change the stake to `5` and place the bet.
4. Without reloading, try another €5 bet.
5. Via the API, send a stake above the balance.

**Expected Result:**
- Step 2: `Insufficient balance` is shown and Place Bet is disabled.
- Step 3: the bet succeeds and every displayed balance drops by €5.
- Steps 4–5: the bet is rejected (422 from the API) and the balance never goes below €0.

### Test-Case-03: Stake limits and format are enforced by the API

**Priority:** Critical

**Risk Rationale:** The stake limits are risk controls, and the API is where they are really enforced. A gap here allows out-of-range or negative stakes that change balances. The spec also contradicts itself on the minimum (€1.00 in §3 and §4.4, €1.01 in §4.1).

**Preconditions:** Reset the balance before each stake, so valid stakes can't fail on insufficient funds.

**Steps:** `POST /api/place-bet` with each stake below, then check the balance.

| Stake | Expected |
|---|---|
| `0.99`, `0`, `-5` | 422 `invalid_stake_min` |
| `1.00`, `1.01`, `100.00` | 200 (€1.00 flagged as a spec conflict) |
| `100.01` | 422 `invalid_stake_max` |
| `1.005` | 422 `invalid_stake_precision` |
| `"10"`, `"abc"`, `null` | 422 `invalid_stake_type` |

**Expected Result:** Rejected stakes leave the balance unchanged. Accepted stakes deduct exactly the stake, with `currency: "EUR"` and `payout = stake × odds`.

### Test-Case-04: Failed placement shows the error modal; Rebet and Close work

**Priority:** High

**Risk Rationale:** Failures happen in production. If one is hidden, or a Rebet places the bet twice, the customer loses trust or is charged twice.

**Steps:**
1. Block `/api/place-bet` (DevTools → *Block request URL*).
2. Place a bet.
3. Unblock and click **Rebet**.
4. Repeat, clicking **Close** and then **X**.

**Expected Result:**
- The modal shows `Something went wrong` with a retry message, and no money is taken.
- Rebet places the bet once.
- Close and X clear the selection and stake.

*Automated as a bonus test.*

### Test-Case-05: Bet slip replaces selections and calculates the payout

**Priority:** Medium

**Risk Rationale:** A wrong slip misleads the customer before they bet. The impact is lower because they can still correct it, and the server re-prices every bet.

**Steps:**
1. Click odds `2` then `1` on one match, then `X` on another.
2. Enter stakes `1`, `1.01` and `15.51`.
3. Use the per-selection **x**, then **Remove All**.

**Expected Result:**
- Only the latest selection is shown and highlighted.
- The payout equals stake × odds rounded to cents, updated as you type.
- Removing clears the slip.

### Test-Case-06: API rejects bad, unauthorised and unsupported requests

**Priority:** Medium

**Risk Rationale:** Wrong error codes hide real outages in monitoring and confuse API clients. No money moves on its own here, so the risk is lower.

**Steps:** Send each request below.

**Expected Result:** The status in the table, and no change to the balance.

| Request | Expected |
|---|---|
| Missing, blank or unknown `x-user-id` | 401 |
| Malformed JSON; array or `null` body | 400 |
| `GET`, `PUT`, `DELETE`, `PATCH` on `/api/place-bet` | 405 |
| Two bets sent at the same time | one 200, one 409 |
| Unknown match, lowercase selection | 422 |
