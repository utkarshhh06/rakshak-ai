
"""Transparent, illustrative transaction-pattern rules for Rakshak AI.

This demo heuristic is not a calibrated fraud probability or a
production detector.
"""

import math
from datetime import datetime, timedelta


RULES = {
    "R-01": {"name": "New beneficiary", "points": 20},
    "R-02": {"name": "Two transfers in 10 minutes", "points": 15},
    "R-03": {"name": "Three or more transfers in 10 minutes", "points": 30},
    "R-04": {"name": "Amount at least 2x typical", "points": 15},
    "R-05": {"name": "Amount at least 3x typical", "points": 25},
    "R-06": {"name": "Reported urgency or impersonation", "points": 25},
}


def risk_band(score: int) -> str:
    """Convert a valid illustrative score from 0 to 100 into a risk band."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("Score must be an integer from 0 to 100.")

    if not 0 <= score <= 100:
        raise ValueError("Score must be an integer from 0 to 100.")

    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def _validate_positive_finite_number(value, field_name: str) -> None:
    """Reject booleans, non-numbers, non-finite values, and values <= 0."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{field_name} must be a finite positive number.")


def analyze_transaction(
    *,
    amount: float,
    typical_amount: float,
    is_new_beneficiary: bool,
    transfers_in_10m: int,
    urgency_or_impersonation_reported: bool,
) -> dict:
    """Validate inputs and return a score plus auditable rule evidence."""
    _validate_positive_finite_number(amount, "Transaction amount")
    _validate_positive_finite_number(
        typical_amount, "Typical transaction amount"
    )

    if (
        isinstance(transfers_in_10m, bool)
        or not isinstance(transfers_in_10m, int)
        or transfers_in_10m < 1
    ):
        raise ValueError(
            "Transfers in the 10-minute window must be an integer of at least 1."
        )

    if (
        not isinstance(is_new_beneficiary, bool)
        or not isinstance(urgency_or_impersonation_reported, bool)
    ):
        raise ValueError("Boolean indicators must be true or false.")

    ratio = amount / typical_amount

    # Finite inputs can still produce a ratio too large for a float.
    if not math.isfinite(ratio):
        raise ValueError(
            "Transaction amount divided by typical amount is too large to represent."
        )

    triggered = []

    def add(rule_id: str, evidence: str) -> None:
        rule = RULES[rule_id]
        triggered.append(
            {
                "rule_id": rule_id,
                "name": rule["name"],
                "points": rule["points"],
                "evidence": evidence,
            }
        )

    if is_new_beneficiary:
        add(
            "R-01",
            "The selected synthetic scenario marks this beneficiary as new.",
        )

    if transfers_in_10m >= 3:
        add(
            "R-03",
            f"{transfers_in_10m} transfers are counted in the 10-minute window.",
        )
    elif transfers_in_10m == 2:
        add(
            "R-02",
            "Exactly 2 transfers are counted in the 10-minute window.",
        )

    if ratio >= 3:
        add(
            "R-05",
            f"Amount is {ratio:.1f}x the typical transaction amount.",
        )
    elif ratio >= 2:
        add(
            "R-04",
            f"Amount is {ratio:.1f}x the typical transaction amount.",
        )

    if urgency_or_impersonation_reported:
        add(
            "R-06",
            "The synthetic scenario includes a user-reported "
            "urgency/impersonation signal.",
        )

    raw_score = sum(item["points"] for item in triggered)
    score = min(raw_score, 100)
    band = risk_band(score)

    guidance = {
        "Low": (
            "No strong warning was triggered by these demo rules. "
            "This does not guarantee the transaction is safe."
        ),
        "Medium": (
            "Review the details and independently verify the beneficiary "
            "or request before proceeding."
        ),
        "High": (
            "Pause and verify the request through a separately obtained "
            "official channel. Consider human review."
        ),
    }[band]

    return {
        "score": score,
        "raw_score": raw_score,
        "risk_band": band,
        "triggered_rules": triggered,
        "guidance": guidance,
        "amount_ratio": round(ratio, 2),
        "transfers_in_10m": transfers_in_10m,
    }


def count_transfers_in_window(
    timestamps,
    target_index: int,
    window_minutes: int = 10,
) -> int:
    """Count events in the inclusive prior window, including the target."""
    if not isinstance(timestamps, (list, tuple)) or not timestamps:
        raise ValueError("A non-empty timestamp list or tuple is required.")

    if (
        isinstance(target_index, bool)
        or not isinstance(target_index, int)
        or target_index < 0
        or target_index >= len(timestamps)
    ):
        raise ValueError("A valid target index is required.")

    if (
        isinstance(window_minutes, bool)
        or not isinstance(window_minutes, int)
        or window_minutes <= 0
    ):
        raise ValueError("Window must be a positive integer number of minutes.")

    if not all(isinstance(ts, datetime) for ts in timestamps):
        raise ValueError("All timestamps must be datetime objects.")

    target = timestamps[target_index]
    start = target - timedelta(minutes=window_minutes)

    return sum(1 for ts in timestamps if start <= ts <= target)
