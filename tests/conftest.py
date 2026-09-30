import warnings
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver

from framework import config
from framework.api_client import BettingApiClient

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "reports" / "screenshots"


@pytest.fixture(scope="session")
def api_client() -> Iterator[BettingApiClient]:
    client = BettingApiClient(config.BASE_URL, config.USER_ID)
    yield client
    client.close()


@pytest.fixture(scope="session")
def match(api_client: BettingApiClient) -> dict:
    """First upcoming match from the live catalog, so no test data is hardcoded.

    Past matches are skipped: they shouldn't be bettable (BUG-10).
    """
    # After today in UTC, so a match that may already have kicked off is never picked.
    today = datetime.now(UTC).date().isoformat()
    upcoming = [m for m in api_client.get_matches() if m["kickoffDate"] > today]
    assert upcoming, "GET /api/matches returned no upcoming matches"
    return upcoming[0]


@pytest.fixture
def starting_balance(api_client: BettingApiClient) -> Decimal:
    return api_client.reset_balance()


@pytest.fixture
def driver() -> Iterator[WebDriver]:
    options = webdriver.ChromeOptions()
    if config.IS_HEADLESS:
        options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    chrome = webdriver.Chrome(options=options)
    yield chrome
    chrome.quit()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item):
    """Save a screenshot when a UI test fails."""
    report = yield
    driver_fixture = getattr(item, "funcargs", {}).get("driver")
    if report.when == "call" and report.failed and driver_fixture is not None:
        try:  # a failed screenshot must never hide the real test failure
            SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
            if not driver_fixture.save_screenshot(str(SCREENSHOT_DIR / f"{item.name}.png")):
                warnings.warn(f"Screenshot not saved for {item.name}", stacklevel=1)
        except (OSError, WebDriverException) as error:
            warnings.warn(f"Screenshot failed for {item.name}: {error}", stacklevel=1)
    return report
