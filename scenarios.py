
"""Fictional scenarios only; no real financial/customer information."""

import math
from datetime import datetime, timedelta

import pandas as pd

from detector import count_transfers_in_window


SCENARIOS = {
    "Normal activity": {
        "amounts": [180, 420, 750, 900],
        "new": False,
        "reported": False,
        "description": "Ordinary low-frequency activity with an established beneficiary.",
        "spacing": 30,
    },
    "New beneficiary": {
        "amounts": [650],
        "new": True,
        "reported": False,
        "description": "A single transfer to a beneficiary marked as new.",
        "spacing": 3,
    },
    "Rapid transfers to a new beneficiary": {
        "amounts": [4900, 4800, 4700],
        "new": True,
        "reported": False,
        "description": "Several transfers close together to a newly added beneficiary.",
        "spacing": 3,
    },
    "Urgency / impersonation indicators": {
        "amounts": [8500, 7900],
        "new": True,
        "reported": True,
        "description": (
            "A new beneficiary plus a user-reported "
            "urgency/impersonation indicator."
        ),
        "spacing": 3,
    },
    "Unusual amount": {
        "amounts": [6500],
        "new": False,
        "reported": False,
        "description": "One amount substantially above the selected typical amount.",
        "spacing": 3,
    },
    "Combined warning indicators": {
        "amounts": [25000, 24000, 23000],
        "new": True,
        "reported": True,
        "description": "Multiple warning signals combined in a fictional scenario.",
        "spacing": 3,
    },
}


def build_scenario(name: str, typical_amount: float) -> pd.DataFrame:
    """Build a fictional scenario with relative transaction timestamps."""

    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}")

    # Reject booleans, non-numeric values, infinity, NaN, and nonpositive amounts.
    if (
        isinstance(typical_amount, bool)
        or not isinstance(typical_amount, (int, float))
        or not math.isfinite(typical_amount)
        or typical_amount <= 0
    ):
        raise ValueError(
            "Typical transaction amount must be a finite positive number."
        )

    config = SCENARIOS[name]
    amounts = config["amounts"]
    spacing = config["spacing"]

    now = datetime.now().replace(second=0, microsecond=0)

    # Generate timestamps once and count transactions in the inclusive
    # ten-minute window ending at each transaction.
    timestamps = [
        now - timedelta(minutes=(len(amounts) - index - 1) * spacing)
        for index in range(len(amounts))
    ]

    rows = []

    for index, amount in enumerate(amounts):
        transaction_time = timestamps[index]

        transfers_in_10m = count_transfers_in_window(
            timestamps,
            target_index=index,
            window_minutes=10,
        )

        rows.append(
            {
                "time": transaction_time,
                "amount_inr": amount,
                "beneficiary_label": (
                    "New demo beneficiary"
                    if config["new"]
                    else "Demo beneficiary A"
                ),
                "is_new_beneficiary": config["new"],
                "transfers_in_10m": transfers_in_10m,
                "urgency_or_impersonation_reported": config["reported"],
                "scenario": name,
                "typical_amount": float(typical_amount),
            }
        )

    return pd.DataFrame(rows)
