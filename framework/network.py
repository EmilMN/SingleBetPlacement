"""Fault injection: make the browser fail matching requests (Chrome DevTools Protocol)."""

from collections.abc import Iterator
from contextlib import contextmanager

from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver

PLACE_BET_URL_PATTERN = "*/api/place-bet*"


@contextmanager
def requests_blocked(driver: ChromeDriver, url_pattern: str) -> Iterator[None]:
    """Fail every request matching url_pattern while inside the block."""
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": [url_pattern]})
    try:
        yield
    finally:
        driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": []})
