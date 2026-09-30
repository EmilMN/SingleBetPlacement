"""Main page: header balance, match list and bet slip."""

from contextlib import suppress
from decimal import Decimal

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from framework import config
from framework.money import parse_money
from framework.pages.receipt_modal import ReceiptModal


class BettingPage:
    HEADER_BALANCE = (By.ID, "header-balance")
    MATCH_LIST = (By.ID, "match-list")
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    TOTAL_STAKE = (By.ID, "bet-slip-total-stake")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    PLACE_BET_BUTTON = (By.ID, "bet-slip-place-bet")

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, config.UI_TIMEOUT_SECONDS)

    def open(self) -> "BettingPage":
        self._driver.get(f"{config.BASE_URL}/?user-id={config.USER_ID}")
        self._wait.until(ec.visibility_of_element_located(self.MATCH_LIST))
        # Balance loads asynchronously and shows €0.00 until then.
        self._wait.until(lambda _: self.get_header_balance() != 0)
        return self

    def get_header_balance(self) -> Decimal:
        return parse_money(self._text(self.HEADER_BALANCE))

    def wait_for_header_balance(self, expected: Decimal) -> Decimal:
        """Give the header time to update; return the last value seen, right or wrong."""
        with suppress(TimeoutException):  # the caller's assertion reports a wrong value
            self._wait.until(lambda _: self.get_header_balance() == expected)
        return self.get_header_balance()

    def select_odds(self, match_id: str, selection: str) -> None:
        button_id = f"odds-{match_id}-{selection.lower()}"  # HOME -> odds-<id>-home
        self._wait.until(ec.element_to_be_clickable((By.ID, button_id))).click()
        self._wait.until(ec.visibility_of_element_located(self.STAKE_INPUT))

    def enter_stake(self, stake: Decimal) -> None:
        stake_input = self._driver.find_element(*self.STAKE_INPUT)
        stake_input.clear()
        stake_input.send_keys(str(stake))
        # Wait for the slip to re-render, so the payout is never read stale.
        self._wait.until(lambda _: parse_money(self._text(self.TOTAL_STAKE)) == stake)

    def get_potential_payout(self) -> Decimal:
        return parse_money(self._text(self.POTENTIAL_PAYOUT))

    def click_place_bet(self) -> None:
        self._wait.until(ec.element_to_be_clickable(self.PLACE_BET_BUTTON)).click()

    def place_bet(self) -> ReceiptModal:
        self.click_place_bet()
        return ReceiptModal(self._driver).wait_until_visible()

    def _text(self, locator: tuple[str, str]) -> str:
        return self._wait.until(ec.visibility_of_element_located(locator)).text
