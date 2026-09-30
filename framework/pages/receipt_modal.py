"""Success receipt shown after a bet is placed (spec §2.4)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from framework import config
from framework.money import parse_money


class ReceiptModal:
    MODAL = (By.ID, "modal-success")
    BET_ID = (By.ID, "modal-success-bet-id")
    MATCH = (By.ID, "modal-success-match")
    STAKE = (By.ID, "modal-success-stake")
    ODDS = (By.ID, "modal-success-odds")
    PAYOUT = (By.ID, "modal-success-payout")
    CLOSE_BUTTON = (By.ID, "modal-success-close")

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, config.PLACEMENT_TIMEOUT_SECONDS)

    def wait_until_visible(self) -> "ReceiptModal":
        self._wait.until(ec.visibility_of_element_located(self.BET_ID))
        return self

    def get_bet_id(self) -> str:
        return self._text(self.BET_ID)

    def read_details(self) -> dict:
        return {
            "match": self._text(self.MATCH),
            "stake": parse_money(self._text(self.STAKE)),
            "odds": parse_money(self._text(self.ODDS)),
            "payout": parse_money(self._text(self.PAYOUT)),
        }

    def close(self) -> None:
        self._wait.until(ec.element_to_be_clickable(self.CLOSE_BUTTON)).click()
        self._wait.until(ec.invisibility_of_element_located(self.MODAL))

    def _text(self, locator: tuple[str, str]) -> str:
        return self._driver.find_element(*locator).text
