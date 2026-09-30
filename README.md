# Single Bet Placement

**Note:** the [CI run](https://github.com/EmilMN/SingleBetPlacement/actions/workflows/tests.yml) shows as failing on purpose. Two of the three automated tests fail because they catch real bugs in the app (see below).

| Parts |
|---|
| [Test plan](TEST_PLAN.md): 6 prioritised scenarios |
| [Execution results and bug reports](BUG_REPORTS.md): 18 bugs, 3 critical |
| Automation framework: this README, [`framework/`](framework), [`tests/`](tests) |
| [Strategy and recommendations](STRATEGY.md) |

## Automated tests

| Test | Type | Checks | Result |
|---|---|---|---|
| `ui/test_bet_placement_journey.py` | E2E UI | Place a bet: receipt and balance match the bet slip and the server | ❌ BUG-02, 04, 05 |
| `api/test_place_bet_rules.py` | API | A stake above the balance is rejected | ❌ BUG-01 |
| `ui/test_bet_placement_failure.py` | E2E UI (bonus) | Failed placement shows the error modal; Rebet charges exactly once | ✅ |

**The two red tests are expected.** They fail on real bugs documented in the bug reports. The UI test reports every mismatch in one run:

```
{'payout': Decimal('20.00')} != {'payout': Decimal('27.50')}
{'match': 'Liverpool vs Tottenham'} != {'match': 'Tottenham vs Liverpool'}
{'header_balance': Decimal('120.00')} != {'header_balance': Decimal('110.00')}
```

The bonus test simulates a failure by blocking the bet request in the browser.

## Setup

Needs Python 3.12+ and Google Chrome. Selenium downloads the matching chromedriver automatically.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
pytest               # all tests
pytest -m api        # API only
pytest -m ui         # UI only
HEADLESS=0 pytest    # watch the browser (PowerShell: $env:HEADLESS="0"; pytest)
```

Failed UI tests save a screenshot to `reports/screenshots/`.
Settings (`BASE_URL`, `USER_ID`, `HEADLESS`) are in [`framework/config.py`](framework/config.py) and can be overridden with environment variables.

**CI:** [GitHub Actions](.github/workflows/tests.yml) runs lint, the API tests and the headless UI tests on every push, and uploads reports and screenshots.

## Design choices

- **Page objects with `id` locators.** Tests read like the user journey, and UI changes are fixed in one place.
- **Setup via the API, checks on both layers.** Fast, reliable setup; the UI test checks what the customer sees *and* what the server stored.
- **No hardcoded test data.** The first upcoming match, its teams and odds come from the live API.
- **The reset endpoint's response isn't trusted.** It reports a different balance from the one it stores (BUG-07), so tests read the balance back.
- **`Decimal` for money**, and explicit waits instead of sleeps.

Tests share one user account, so they run one at a time.

Tooling: pytest 9, Selenium 4.49, requests 2.34, ruff for linting.

AI tools were used for assistance (review, scaffolding, second opinions); test strategy, prioritisation and bug triage were verified and owned by me.
