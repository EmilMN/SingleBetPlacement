from decimal import Decimal

import pytest

from framework import config
from framework.api_client import BettingApiClient
from framework.money import CENT


@pytest.mark.api
def test_stake_exceeding_available_balance_is_rejected(
    api_client: BettingApiClient, match: dict, starting_balance: Decimal
) -> None:
    """A stake one cent above the balance must be rejected and move no money.

    Why: it stops customers betting money they don't have (spec §4.1). The UI check can
    be bypassed or stale, so the API is where this rule must hold.
    """
    # Spend down first: balance + 1 cent must stay under the €100 max stake,
    # so the balance rule is the only rule being broken.
    max_stake = config.MAX_STAKE
    assert max_stake < starting_balance < 2 * max_stake, "Setup needs a €100-200 balance"
    spend_down = api_client.place_bet(match["id"], "HOME", max_stake)
    assert spend_down.status_code == 200, f"Setup bet failed: {spend_down.text}"
    balance_before = api_client.get_balance()
    assert balance_before == starting_balance - max_stake

    stake = balance_before + CENT
    response = api_client.place_bet(match["id"], "HOME", stake)

    assert response.status_code == 422, (
        f"Stake {stake} with balance {balance_before} was accepted: {response.text}"
    )
    assert response.json()["error"] == "insufficient_balance"  # code from the OpenAPI spec
    assert api_client.get_balance() == balance_before, "Rejected bet must not move money"
