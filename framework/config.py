"""Test settings. Override any of them with an environment variable."""

import os
from decimal import Decimal

BASE_URL = os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app").rstrip("/")
USER_ID = os.getenv("USER_ID", "candidate-CPkDP9YYtK7Q")
IS_HEADLESS = os.getenv("HEADLESS", "1").lower() not in ("0", "false")

API_TIMEOUT_SECONDS = 15
UI_TIMEOUT_SECONDS = 10
PLACEMENT_TIMEOUT_SECONDS = 20  # the app delays placement by up to ~4.5 s

MAX_STAKE = Decimal("100.00")  # spec §3
