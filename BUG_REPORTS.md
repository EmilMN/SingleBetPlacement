# Execution Results & Bug Reports

**Run on:** 2026-09-29/30, Chrome on Windows 11, user `candidate-CPkDP9YYtK7Q`. The API was called with curl. Tottenham vs Liverpool (1 Oct) was the next upcoming match on those dates.

**Scope:** the top 3 scenarios from the [test plan](TEST_PLAN.md), plus exploratory testing of the whole betting flow.

## Results

| ID | Scenario | Result | Bugs |
|---|---|---|---|
| Test-Case-01 | Valid bet; receipt and balance consistent | ❌ Fail | BUG-02, 04, 05, 06, 07 |
| Test-Case-02 | Stake above balance rejected | ❌ Fail | BUG-01, 02 |
| Test-Case-03 | Stake limits enforced by the API | ❌ Fail | BUG-03, 08 |

**What worked:**
- The `Placing...` state and the payout on the bet slip.
- The UI blocks bets above the balance, as long as the displayed balance is up to date.
- The API rejects 0.99, 0, 100.01, 1.005 and non-numeric stakes (but not negative ones, BUG-03).

## Summary

The 3 scenarios found 8 bugs (one scenario checks many things, so it can find several). The other 10 came from exploratory testing.

| ID | Title | Severity | Found in |
|---|---|---|---|
| BUG-01 | API accepts stakes above the balance; balance goes negative | Critical | Test-Case-02 |
| BUG-03 | API accepts a negative stake and adds money to the balance | Critical | Test-Case-03 |
| BUG-15 | Clicking Place Bet again while it shows Placing... places another bet | Critical | Exploratory |
| BUG-02 | Balance isn't refreshed after a bet, so customers can overdraw from the UI | High | Test-Case-02 |
| BUG-04 | Receipt payout is stake × 2, ignoring the odds | High | Test-Case-01 |
| BUG-05 | Receipt shows the teams reversed | High | Test-Case-01 |
| BUG-18 | Server's "bet in progress" guard sometimes lets simultaneous bets through | High | Exploratory |
| BUG-06 | Receipt doesn't show the selection | Medium | Test-Case-01 |
| BUG-07 | Reset reports €125.50 but stores €120.00 | Medium | Test-Case-01 (setup) |
| BUG-08 | Bet response says `currency: "USD"` | Medium | Test-Case-03 |
| BUG-09 | Malformed JSON returns 500 instead of 400 | Medium | Exploratory |
| BUG-10 | Past matches appear in the Upcoming list and can be bet on | Medium | Exploratory |
| BUG-13 | Odds filter hides matching matches and accepts invalid ranges | Medium | Exploratory |
| BUG-14 | Receipt Bet ID is a random number made up by the browser | Medium | Exploratory |
| BUG-16 | Date filter misses matches for users west of UTC | Medium | Exploratory |
| BUG-11 | API rounds payout down; the bet slip rounds normally | Low | Exploratory |
| BUG-12 | `GET /api/place-bet` returns 200 instead of 405 | Low | Exploratory |
| BUG-17 | Match count ignores filters | Low | Exploratory |

---

### BUG-01: API accepts stakes above the balance; balance goes negative

**Severity:** Critical

**Reproduction Steps:**
1. `POST /api/reset-balance` (balance €120).
2. `POST /api/place-bet` with `{"matchId":"premier-league-tottenham-liverpool-2026-10-01","selection":"HOME","stake":100}` → balance €20.
3. Send the same request again.

**Expected:** Step 3 returns 422 insufficient balance; the balance stays €20 (spec §4.1).

**Actual:** 200 *Bet placed successfully*, `"balance": -80`.

**Business Impact:** Customers can bet money they don't have. That is a direct loss and a responsible-gambling breach.

**Evidence:** `{"stake":100,"odds":2.75,"payout":275,"balance":-80,"currency":"USD"}`

---

### BUG-03: API accepts a negative stake and adds money to the balance

**Severity:** Critical

**Reproduction Steps:** Send the BUG-01 request with `"stake": -5`.

**Expected:** 422 `invalid_stake_min`.

**Actual:** 200, `"payout": -13.75`, and the balance goes **up** by €5. There is no floor: `-1000` adds €1,000 in one call. A stake of `0` is correctly rejected.

**Business Impact:** Anyone calling the API can add unlimited money to their account.

**Evidence:** `{"stake":-5,"odds":2.75,"payout":-13.75,...}`, balance +€5. A duplicate key also gets through: `{"stake":1,"stake":-50}` is accepted as −50.

---

### BUG-15: Clicking Place Bet again while it shows Placing... places another bet

**Severity:** Critical

**Reproduction Steps:**
1. Reset the balance (€120). Select Tottenham vs Liverpool → `1`, stake `5`.
2. Click **Place Bet**, then click it again while it shows `Placing...` (a double-click does this).
3. Close each receipt, then `GET /api/balance`.

**Expected:** One bet and one receipt. The button is locked while placing, so the result is €115.

**Actual:** Each extra click places another bet. The balance drops to **€110** and two receipts appear one after the other. Occasionally the second bet is rejected with 409 instead, and the customer may see a receipt *and* an error (spec §2.3: "one final outcome").

**Root cause (app code):** the button stays clickable while it shows `Placing...`.

**Business Impact:** A double-click, a very common habit, charges the customer twice. Because the header balance doesn't update (BUG-02), the second charge is easy to miss. This leads to complaints and chargebacks.

**Evidence:** Chrome network log shows 2 × `POST /api/place-bet`; balance 120 → 110; receipts `#B-78318` and `#B-78954`. Double-charged in 13 of 14 runs.

---

### BUG-02: Balance isn't refreshed after a bet, so customers can overdraw from the UI

**Severity:** High

**Reproduction Steps:**
1. With a balance of €5.99, bet €5 in the UI and close the receipt.
2. The header and slip still show €5.99; the server holds €0.99.
3. Bet €5 again.

**Expected:** The balance shows €0.99 after the first bet, and the second bet is blocked with `Insufficient balance`.

**Actual:** The balance only updates after a page reload. The second bet goes through (the API doesn't check either, BUG-01), leaving **−€4.01**.

**Root cause (app code):** after a successful bet the UI never re-fetches `/api/balance`.

**Business Impact:** Every customer sees a wrong balance after each bet. Combined with BUG-01, any customer placing two bets in a row can overdraw.

**Evidence:** [evidence/ui-stale-balance-after-bet.png](evidence/ui-stale-balance-after-bet.png): header €5.99 after the first bet, while the API holds €0.99. After the second bet the API returned `-4.01`.

---

### BUG-04: Receipt payout is stake × 2, ignoring the odds

**Severity:** High

**Reproduction Steps:** Bet €10 on Tottenham (home, 2.75). The slip shows €27.50. Place the bet and check the receipt.

**Expected:** €27.50, matching the slip and the API response.

**Actual:** €20.00. Other bets gave the same pattern:

| Stake | Odds | Expected | Receipt |
|---|---|---|---|
| €10.00 | 2.45 | €24.50 | €20.00 |
| €1.01 | 3.20 | €3.23 | €2.02 |
| €3.00 | 6.00 | €18.00 | €6.00 |

**Root cause (app code):** the receipt uses `potentialPayout: stake * 2`.

**Business Impact:** The customer's record of the bet shows the wrong winnings, which leads to disputes and support contacts.

**Evidence:** [evidence/receipt-swapped-teams-wrong-payout.png](evidence/receipt-swapped-teams-wrong-payout.png) (the €10 @ 2.45 bet)

---

### BUG-05: Receipt shows the teams reversed

**Severity:** High

**Reproduction Steps:** Bet on *Tottenham vs Liverpool* and check the receipt.

**Expected:** "Tottenham vs Liverpool" (home team first).

**Actual:** "Liverpool vs Tottenham". This happens on every match (e.g. "Chelsea vs Manchester Utd" in the screenshot): the app puts the away team first.

**Business Impact:** Together with BUG-06, the customer can't tell which team they backed.

**Evidence:** [evidence/receipt-swapped-teams-wrong-payout.png](evidence/receipt-swapped-teams-wrong-payout.png)

---

### BUG-18: Server's "bet in progress" guard sometimes lets simultaneous bets through

**Severity:** High

**Reproduction Steps:**
1. Reset the balance (€120).
2. Send 8 identical `POST /api/place-bet` requests at the same moment (€1 on Tottenham vs Liverpool).
3. `GET /api/balance`. Repeat a few rounds.

**Expected:** One 200, the rest 409 `bet_in_progress`, and €1 charged (spec §5.3: 409 for a bet already in progress).

**Actual:** Usually one 200, but in some rounds two or three bets are accepted and charged. Two accepted requests were sent within 1 ms of each other and processed at the same time.

**Business Impact:** The server's safety net against duplicate submissions has a gap, so a retry or double submission (see BUG-15) can still charge the customer twice.

**Evidence:** 8 parallel €1 bets per round: charged twice in 1 of 8 rounds (my run) and 2–3 times in 2 of 6 rounds (a separate retest); every other round charged once.

---

### BUG-06: Receipt doesn't show the selection

**Severity:** Medium

**Reproduction Steps:** Place any bet and check the receipt.

**Expected:** The receipt shows Home, Draw or Away (spec §2.4).

**Actual:** The selection is missing. The slip did show "Match Winner: Home".

**Business Impact:** The receipt is incomplete, so the customer can't verify their pick.

**Evidence:** [evidence/receipt-swapped-teams-wrong-payout.png](evidence/receipt-swapped-teams-wrong-payout.png)

---

### BUG-07: Reset reports €125.50 but stores €120.00

**Severity:** Medium

**Reproduction Steps:**
1. `POST /api/reset-balance`
2. `GET /api/balance`

**Expected:** €125.50 in both: the documented starting balance, and spec §5.3 says the response must match what is stored.

**Actual:** The reset returns 125.5, but the stored balance is 120. Every time.

**Business Impact:** Anything that trusts the reset response works from a wrong balance, and each reset leaves the account €5.50 short.

**Evidence:** `POST → {"balance":125.5}`, then `GET → {"balance":120}`

**Note:** The Swagger docs describe the reset response as one that "may differ from persisted balance". That contradicts spec §5.3, which takes priority, so the documents themselves need aligning too.

---

### BUG-08: Bet response says `currency: "USD"`

**Severity:** Medium

**Reproduction Steps:** Place any bet via the API.

**Expected:** `"EUR"` (spec §3).

**Actual:** `"USD"`, while `GET /api/balance` says `"EUR"`.

**Business Impact:** Receipts, statements or reports built on this field would label euros as dollars.

**Evidence:** `{"stake":10,"payout":24.5,"balance":110,"currency":"USD"}`

---

### BUG-09: Malformed JSON returns 500 instead of 400

**Severity:** Medium

**Reproduction Steps:** `POST /api/place-bet` with a truncated body: `{"matchId":"la-liga-real-barca"`

**Expected:** 400 `invalid_json` (spec §4.3).

**Actual:** 500 `internal_server_error`. The same happens for trailing garbage (`{"matchId":"x"}abc`) and a hex stake (`"stake":0x10`).

**Business Impact:** Client mistakes show up as server outages, which triggers false alerts and hides real ones.

**Evidence:** `{"error":"internal_server_error","message":"Unable to process request."}`

---

### BUG-10: Past matches appear in the Upcoming list and can be bet on

**Severity:** Medium

**Reproduction Steps:** On 2026-09-29, 79 of 103 matches are tagged **PAST** but their odds can still be clicked. Bet on *Manchester Utd vs Chelsea* (kickoff 2026-02-27).

**Expected:** Only upcoming matches can be bet on (spec §1, §3).

**Actual:** The bet is accepted.

**Business Impact:** If these were real past events, customers could bet on known results — a direct loss. Rated Medium because the dates may just be stale seed data.

**Evidence:** The PAST tag is visible in the UI, yet `POST /api/place-bet` returned 200.

---

### BUG-13: Odds filter hides matching matches and accepts invalid ranges

**Severity:** Medium

**Reproduction Steps:**
1. Odds filter: Min `2.45`, Max `3.00`, Apply.
2. Odds filter: Min `5`, Max `2`, Apply.

**Expected:** Step 1 shows every match with an odd between 2.45 and 3.00, inclusive (spec §2.6), e.g. Man Utd vs Chelsea (2.45 / 3.10 / 2.80). Step 2 is rejected with clear feedback.

**Actual:**
- Step 1: Man Utd vs Chelsea disappears. The filter excludes any match with an odd *equal* to the minimum, and the minimum itself is exclusive.
- Step 2: the range is applied with no message and the list goes empty.

**Business Impact:** Customers filtering by odds miss matches they would bet on and get no explanation for an empty list.

**Evidence:** [evidence/odds-filter-drops-matching-match.jpg](evidence/odds-filter-drops-matching-match.jpg), [evidence/odds-filter-invalid-range-no-feedback.jpg](evidence/odds-filter-invalid-range-no-feedback.jpg)

---

### BUG-14: Receipt Bet ID is a random number made up by the browser

**Severity:** Medium

**Reproduction Steps:** Place a bet and compare the receipt's Bet ID with the API response.

**Expected:** The Bet ID identifies the bet on the server (spec §2.4).

**Actual:** The API returns no bet id. The receipt shows `#B-` plus a random 5-digit number made up in the browser, so the same id can repeat.

**Business Impact:** Support can't look a bet up from the customer's receipt, and two customers can hold the same "Bet ID".

**Evidence:** `POST /api/place-bet` response fields: message, matchId, selection, stake, odds, payout, balance, currency — no id.

---

### BUG-16: Date filter misses matches for users west of UTC

**Severity:** Medium

**Reproduction Steps:**
1. Set the browser time zone to `America/New_York` (Chrome DevTools → Sensors → Location → add a custom location).
2. Date filter → Custom → 1 October 2026 → Apply.

**Expected:** Tottenham vs Liverpool (kickoff 2026-10-01) is shown, as it is for a user in Berlin.

**Actual:** The list is empty. The filter reads kickoff dates as UTC midnight, which is the previous day in New York.

**Business Impact:** Customers in the Americas filtering by date miss matches, or see them under the wrong day.

**Evidence:** [evidence/date-filter-oct1-berlin.png](evidence/date-filter-oct1-berlin.png) (1 match) and [evidence/date-filter-oct1-new-york.png](evidence/date-filter-oct1-new-york.png) (0 matches): same filter, only the time zone differs. Tokyo also shows 1 match, Los Angeles 0.

---

### BUG-11: API rounds payout down; the bet slip rounds normally

**Severity:** Low

**Reproduction Steps:** Via the API, bet €1.01 on Tottenham at 2.75 (= 2.7775).

**Expected:** The same payout as the slip shows (2.78).

**Actual:** 2.77. €99.99 × 3.10 also gives 309.96 instead of 309.97.

**Business Impact:** The customer sees one payout before betting and gets another. It's at most a cent per bet, but it adds up. Which rounding is correct isn't defined in the spec; the defect is that UI and API disagree.

**Evidence:** `{"stake":1.01,"odds":2.75,"payout":2.77}`

---

### BUG-12: `GET /api/place-bet` returns 200 instead of 405

**Severity:** Low

**Reproduction Steps:** `GET /api/place-bet`

**Expected:** 405. PUT, DELETE and PATCH do return 405.

**Actual:** `200 {}`, even without an `x-user-id` header (every other endpoint returns 401).

**Business Impact:** A misleading success response that can hide client mistakes.

**Evidence:** `GET → 200 {}`

---

### BUG-17: Match count ignores filters

**Severity:** Low

**Reproduction Steps:** Apply any date or odds filter, e.g. odds 2.45–3.00 (23 matches shown).

**Expected:** The count matches the list, e.g. "Showing 23 matches".

**Actual:** Always "Showing 103 matches", even when the list is empty.

**Business Impact:** Misleading, and it makes an empty filtered list look like a loading problem.

**Evidence:** [evidence/odds-filter-invalid-range-no-feedback.jpg](evidence/odds-filter-invalid-range-no-feedback.jpg) (0 matches shown, header says 103)

---

## What held up

- **Error modal** (forced by blocking the request): Close and X both clear the selection and stake; Rebet retries once.
- **Stake input:** it cleans up bad input (`1,5` → `1.5`, `-5` → `5`, `12.345` → `12.34`). A stake equal to the balance is allowed, and one cent above is blocked.
- **While placing:** the odds buttons and stake input are locked, but Place Bet is not (BUG-15).
- **Date filter (Europe):** single day and inclusive ranges are correct, and so is Reset.
- **API:** strict about selection and matchId variants (case, whitespace, types), odds are static for the session, and the catalog has valid odds with no duplicates.

---

## Minor observations

- An empty request body returns 422 `invalid_match_id`; spec §4.3 suggests 400 for a malformed payload.
- Switching to another odds button clears the stake, so the customer has to type it again.
- Enter in the stake field doesn't submit the bet.
- Reloading during `Placing...` silently drops the bet, because the app waits 1–4 s before sending it.
- The API accepts a JSON body sent as `text/plain`.
- With an invalid user ID, the header shows a misleading "Balance: €0.00".

## Spec questions

- **Minimum stake:** €1.00 (§3, §4.4) or €1.01 (§4.1)? The app uses €1.00.
- **Payout rounding:** round half-up or round down? The UI and API differ.
- **Past matches:** should they be hidden, disabled, or rejected by the API?
- **Bet ID:** §2.4 requires one on the receipt, but the §5.3 response has no id. Who issues it?
