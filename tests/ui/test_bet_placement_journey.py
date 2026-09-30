from decimal import Decimal

import pytest
from selenium.webdriver.chrome.webdriver import WebDriver

from framework.api_client import BettingApiClient
from framework.money import calculate_payout, to_money
from framework.pages.betting_page import BettingPage

STAKE = to_money("10.00")


@pytest.mark.ui
def test_place_single_bet_receipt_and_balance_are_consistent(
    driver: WebDriver, api_client: BettingApiClient, match: dict, starting_balance: Decimal
) -> None:
    """Place a bet; the receipt and balance must match the bet slip and the server.

    Why: this is the core revenue journey (Test-Case-01), and the receipt is the customer's
    record of the bet. One test covers bet slip, API, receipt and header balance.
    """
    odds = to_money(match["odds"]["home"])
    expected_payout = calculate_payout(STAKE, odds)

    page = BettingPage(driver).open()
    assert page.get_header_balance() == starting_balance

    page.select_odds(match["id"], "HOME")
    page.enter_stake(STAKE)
    assert page.get_potential_payout() == expected_payout

    receipt = page.place_bet()
    assert receipt.get_bet_id(), "Receipt must show a bet id"
    receipt_details = receipt.read_details()
    receipt.close()

    # Compare everything at once so one run reports every mismatch.
    expected_balance = starting_balance - STAKE
    actual = {
        **receipt_details,
        "header_balance": page.wait_for_header_balance(expected_balance),
        "server_balance": api_client.get_balance(),
    }
    expected = {
        "match": f"{match['homeTeam']} vs {match['awayTeam']}",
        "stake": STAKE,
        "odds": odds,
        "payout": expected_payout,
        "header_balance": expected_balance,
        "server_balance": expected_balance,
    }
    assert actual == expected
