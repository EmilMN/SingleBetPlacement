# Strategy & Recommendations

## Why these 2 tests

I picked the tests with the **highest business risk** that are also **worth running on every build**.

- **E2E UI: place a bet, check receipt and balance (Test-Case-01).** This is the journey the product exists for. One test covers the bet slip, API, receipt and header balance, and manual testing found 4 bugs on this path (BUG-02, 04, 05, 06).
- **API: stake above the balance is rejected.** Letting customers bet money they don't have is the most expensive rule to get wrong. The UI check can be bypassed or stale (BUG-02), so the rule has to hold in the API. API tests are also fast and stable, so they can block a merge.

**Runners-up:**
- **Stake boundaries (Test-Case-03):** the next API test I'd automate, as one parametrised test.
- **Double-click on Place Bet (BUG-15):** the next UI test. It is critical and easy to automate by counting bet requests. The risk exists on both layers: the UI sends duplicates (BUG-15) and the server doesn't reliably reject them (BUG-18).
- **Status codes (Test-Case-06):** lower impact, and better covered by contract tests.
- **Bet slip behaviour (Test-Case-05):** low risk, because the server re-prices every bet.

**Bonus test: error modal and Rebet (Test-Case-04).** Rebet re-sends a payment, so a double charge would be costly. I automated it by blocking the request in the browser. It passes. Close and X are still manual.

## Left manual

- **Exploratory testing.** It found 10 of the 18 bugs, including critical BUG-15: a scripted test wouldn't think to click again during `Placing...`.
- **Copy, layout and visual checks.** These are judgement calls, and automated layout checks break easily.
- **Filters (§2.6).** Calendar and range pickers are costly to automate and lower risk than money flows. Their bugs (BUG-13, BUG-16) are better caught by unit tests, run in more than one time zone.
- **Spec gaps** (min stake €1.00 vs €1.01, payout rounding, past matches). These need a product decision first; a test would only lock in a guess.

## Recommendations for scale

1. **CI with fast feedback.** The included [GitHub Actions workflow](.github/workflows/tests.yml) already runs lint, the API tests and the UI tests on every push. Next steps:
   - make API tests a required check for merging;
   - run the UI suite nightly;
   - publish an Allure report.
2. **Test data and layers.**
   - Give each parallel worker its own user, so tests can run in parallel.
   - Add a reliable endpoint to set a balance directly, replacing the buggy reset.
   - Generate contract tests from the OpenAPI spec. They would catch BUG-09 today, and BUG-08 and BUG-14 once the spec lists the allowed currency and a bet id.
   - Unit-test the payout calculation, where BUG-04 and BUG-11 come from.
3. **Clarify the spec.** Settle the minimum stake (€1.00 vs €1.01), the payout rounding rule, how past matches should appear, and who issues the Bet ID. Each answer becomes an acceptance test.
