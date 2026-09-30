from decimal import Decimal

import pytest
from selenium.webdriver.chrome.webdriver import WebDriver

from framework.api_client import BettingApiClient
from framework.money import to_money
from framework.network import PLACE_BET_URL_PATTERN, requests_blocked
from framework.pages.betting_page import BettingPage
from framework.pages.error_modal import ErrorModal

STAKE = to_money("2.00")


@pytest.mark.ui
def test_rebet_after_failed_placement_charges_exactly_once(
    driver: WebDriver, api_client: BettingApiClient, match: dict, starting_balance: Decimal
) -> None:
    """A failed placement shows the error modal; Rebet then charges exactly once.

    Why: Rebet re-sends a money transaction, so a double charge is the costly failure.
    Failures can't be triggered from the UI, so the browser blocks the request (Test-Case-04).
    """
    page = BettingPage(driver).open()
    page.select_odds(match["id"], "HOME")
    page.enter_stake(STAKE)

    with requests_blocked(driver, PLACE_BET_URL_PATTERN):
        page.click_place_bet()
        error_modal = ErrorModal(driver).wait_until_visible()

    assert "Something went wrong" in error_modal.get_text()
    assert api_client.get_balance() == starting_balance, "No bet may be placed while blocked"

    error_modal.rebet()
    assert api_client.get_balance() == starting_balance - STAKE, "Rebet must charge once"
