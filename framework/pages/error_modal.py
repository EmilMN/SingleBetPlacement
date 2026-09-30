"""Page object for the error modal shown when bet placement fails (spec §2.5)."""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from framework import config
from framework.pages.receipt_modal import ReceiptModal


class ErrorModal:
    MODAL = (By.ID, "modal-error")
    REBET_BUTTON = (By.ID, "modal-error-rebet")

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver
        self._wait = WebDriverWait(driver, config.PLACEMENT_TIMEOUT_SECONDS)

    def wait_until_visible(self) -> "ErrorModal":
        self._wait.until(ec.visibility_of_element_located(self.MODAL))
        return self

    def get_text(self) -> str:
        return self._driver.find_element(*self.MODAL).text

    def rebet(self) -> ReceiptModal:
        self._wait.until(ec.element_to_be_clickable(self.REBET_BUTTON)).click()
        return ReceiptModal(self._driver).wait_until_visible()
