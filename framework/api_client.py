"""Client for the Sports Betting API (spec §5)."""

from decimal import Decimal

import requests

from framework import config
from framework.money import to_money


class BettingApiClient:
    def __init__(self, base_url: str, user_id: str) -> None:
        self._base_url = base_url
        self._session = requests.Session()
        self._session.headers.update({"x-user-id": user_id})

    def close(self) -> None:
        self._session.close()

    def get_matches(self) -> list[dict]:
        return self._get_json("/api/matches")

    def get_balance(self) -> Decimal:
        return to_money(self._get_json("/api/balance")["balance"])

    def reset_balance(self) -> Decimal:
        """Reset and return the balance the server stored.

        The reset response is ignored: it doesn't match the stored balance (BUG-07).
        """
        self._request("POST", "/api/reset-balance").raise_for_status()
        return self.get_balance()

    def place_bet(self, match_id: str, selection: str, stake: Decimal) -> requests.Response:
        """Returns the raw response so tests can check rejections too."""
        payload = {"matchId": match_id, "selection": selection, "stake": float(stake)}
        return self._request("POST", "/api/place-bet", json=payload)

    def _get_json(self, path: str):
        response = self._request("GET", path)
        response.raise_for_status()
        return response.json()

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self._base_url}{path}"
        return self._session.request(method, url, timeout=config.API_TIMEOUT_SECONDS, **kwargs)
