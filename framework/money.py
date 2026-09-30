"""Money helpers. Decimal avoids float rounding errors when comparing euro amounts."""

import re
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
_AMOUNT = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def to_money(value: float | str | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def parse_money(text: str) -> Decimal:
    """'Balance: €120.00' -> Decimal('120.00')"""
    match = _AMOUNT.search(text)
    if match is None:
        raise ValueError(f"No amount found in {text!r}")
    return to_money(match.group().replace(",", ""))


def calculate_payout(stake: Decimal, odds: Decimal) -> Decimal:
    """Payout = stake x odds (includes the stake), rounded to cents."""
    return to_money(stake * odds)
