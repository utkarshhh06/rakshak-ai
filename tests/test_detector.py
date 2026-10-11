import pytest
from detector import analyze_transaction, risk_band

import pytest
from datetime import datetime, timedelta

from detector import (
    analyze_transaction,
    risk_band,
    count_transfers_in_window,
)

BASE = dict(amount=1000, typical_amount=1000, is_new_beneficiary=False,
            transfers_in_10m=1, urgency_or_impersonation_reported=False)

def test_normal_is_low_with_no_rules():
    result = analyze_transaction(**BASE)
    assert result["score"] == 0
    assert result["risk_band"] == "Low"
    assert result["triggered_rules"] == []

def test_new_beneficiary_adds_20():
    result = analyze_transaction(**{**BASE, "is_new_beneficiary": True})
    assert result["score"] == 20
    assert [r["rule_id"] for r in result["triggered_rules"]] == ["R-01"]

def test_velocity_rules_are_exclusive():
    two = analyze_transaction(**{**BASE, "transfers_in_10m": 2})
    three = analyze_transaction(**{**BASE, "transfers_in_10m": 3})
    assert [r["rule_id"] for r in two["triggered_rules"]] == ["R-02"]
    assert [r["rule_id"] for r in three["triggered_rules"]] == ["R-03"]

def test_amount_boundaries_are_exclusive():
    two_x = analyze_transaction(**{**BASE, "amount": 2000})
    three_x = analyze_transaction(**{**BASE, "amount": 3000})
    assert [r["rule_id"] for r in two_x["triggered_rules"]] == ["R-04"]
    assert [r["rule_id"] for r in three_x["triggered_rules"]] == ["R-05"]

def test_combined_indicators_score_100():
    result = analyze_transaction(amount=3000, typical_amount=1000, is_new_beneficiary=True,
        transfers_in_10m=3, urgency_or_impersonation_reported=True)
    assert result["score"] == 100
    assert result["risk_band"] == "High"

def test_invalid_amount_rejected():
    with pytest.raises(ValueError):
        analyze_transaction(**{**BASE, "amount": 0})

def test_invalid_baseline_rejected():
    with pytest.raises(ValueError):
        analyze_transaction(**{**BASE, "typical_amount": 0})

def test_risk_band_boundaries():
    assert risk_band(29) == "Low"
    assert risk_band(30) == "Medium"
    assert risk_band(59) == "Medium"
    assert risk_band(60) == "High"


def test_window_includes_transaction_exactly_10_minutes_old():
    base = datetime(2026, 10, 10, 12, 0, 0)
    timestamps = [
        base,
        base + timedelta(minutes=5),
        base + timedelta(minutes=10),
    ]
    assert count_transfers_in_window(timestamps, 2) == 3


def test_window_excludes_transaction_older_than_10_minutes():
    base = datetime(2026, 10, 10, 12, 0, 0)
    timestamps = [
        base,
        base + timedelta(seconds=1),
        base + timedelta(minutes=10, seconds=1),
    ]
    assert count_transfers_in_window(timestamps, 2) == 2


def test_window_counts_only_events_at_or_before_target():
    base = datetime(2026, 10, 10, 12, 0, 0)
    timestamps = [
        base,
        base + timedelta(minutes=3),
        base + timedelta(minutes=11),
    ]
    assert count_transfers_in_window(timestamps, 1) == 2


def test_window_rejects_invalid_target_index():
    with pytest.raises(ValueError):
        count_transfers_in_window([], 0)

    with pytest.raises(ValueError):
        count_transfers_in_window(
            [datetime(2026, 10, 10, 12, 0)],
            1,
        )


def test_window_rejects_non_datetime_target():
    with pytest.raises(ValueError):
        count_transfers_in_window(
            ["not-a-timestamp"],
            0,
        )


def test_window_rejects_invalid_window_length():
    timestamps = [datetime(2026, 10, 10, 12, 0)]

    for invalid_window in (0, -1, 1.5, True):
        with pytest.raises(ValueError):
            count_transfers_in_window(
                timestamps,
                0,
                window_minutes=invalid_window,
            )

@pytest.mark.parametrize(
    "invalid_value",
    [float("inf"), float("-inf"), float("nan")],
)
def test_non_finite_transaction_amount_is_rejected(invalid_value):
    with pytest.raises(ValueError):
        analyze_transaction(
            amount=invalid_value,
            typical_amount=1000,
            is_new_beneficiary=False,
            transfers_in_10m=1,
            urgency_or_impersonation_reported=False,
        )


@pytest.mark.parametrize(
    "invalid_value",
    [float("inf"), float("-inf"), float("nan")],
)
def test_non_finite_typical_amount_is_rejected(invalid_value):
    with pytest.raises(ValueError):
        analyze_transaction(
            amount=1000,
            typical_amount=invalid_value,
            is_new_beneficiary=False,
            transfers_in_10m=1,
            urgency_or_impersonation_reported=False,
        )


def test_unrepresentable_amount_ratio_is_rejected():
    with pytest.raises(ValueError):
        analyze_transaction(
            amount=1e308,
            typical_amount=1e-308,
            is_new_beneficiary=False,
            transfers_in_10m=1,
            urgency_or_impersonation_reported=False,
        )


def test_boolean_target_index_is_rejected():
    timestamps = [datetime(2026, 1, 1, 12, 0)]

    with pytest.raises(ValueError):
        count_transfers_in_window(timestamps, True)


def test_non_datetime_in_timestamp_list_is_rejected():
    timestamps = [
        datetime(2026, 1, 1, 12, 0),
        "not a datetime",
    ]

    with pytest.raises(ValueError):
        count_transfers_in_window(timestamps, 0)

# Additional regression tests for detection logic.
# These tests preserve the existing scoring rules and API.

import math
import pytest

from datetime import datetime, timedelta

from detector import (
    RULES,
    analyze_transaction,
    count_transfers_in_window,
    risk_band,
)


def analyze_default(**overrides):
    values = {
        "amount": 1000.0,
        "typical_amount": 1000.0,
        "is_new_beneficiary": False,
        "transfers_in_10m": 1,
        "urgency_or_impersonation_reported": False,
    }
    values.update(overrides)
    return analyze_transaction(**values)


@pytest.mark.parametrize("bad_amount", [
    0,
    -1,
    True,
    float("inf"),
    float("-inf"),
    float("nan"),
    "1000",
    None,
])
def test_invalid_transaction_amount_rejected(bad_amount):
    with pytest.raises(ValueError):
        analyze_default(amount=bad_amount)


@pytest.mark.parametrize("bad_amount", [
    0,
    -1,
    True,
    float("inf"),
    float("-inf"),
    float("nan"),
    "1000",
    None,
])
def test_invalid_typical_amount_rejected(bad_amount):
    with pytest.raises(ValueError):
        analyze_default(typical_amount=bad_amount)


def test_extreme_amount_ratio_rejected():
    with pytest.raises(ValueError):
        analyze_default(
            amount=1e308,
            typical_amount=1e-308,
        )


@pytest.mark.parametrize("count", [0, -1, True, 1.5, "3", None])
def test_invalid_transfer_count_rejected(count):
    with pytest.raises(ValueError):
        analyze_default(transfers_in_10m=count)


@pytest.mark.parametrize(
    "amount, expected_rule",
    [
        (1999.99, None),
        (2000, "R-04"),
        (2999.99, "R-04"),
        (3000, "R-05"),
        (8000, "R-05"),
    ],
)
def test_amount_rule_boundaries(amount, expected_rule):
    result = analyze_default(amount=amount)

    amount_rules = [
        rule["rule_id"]
        for rule in result["triggered_rules"]
        if rule["rule_id"] in ("R-04", "R-05")
    ]

    if expected_rule is None:
        assert amount_rules == []
    else:
        assert amount_rules == [expected_rule]


@pytest.mark.parametrize(
    "count, expected_rule",
    [
        (1, None),
        (2, "R-02"),
        (3, "R-03"),
        (4, "R-03"),
    ],
)
def test_transfer_rule_boundaries(count, expected_rule):
    result = analyze_default(transfers_in_10m=count)

    transfer_rules = [
        rule["rule_id"]
        for rule in result["triggered_rules"]
        if rule["rule_id"] in ("R-02", "R-03")
    ]

    if expected_rule is None:
        assert transfer_rules == []
    else:
        assert transfer_rules == [expected_rule]


@pytest.mark.parametrize(
    "score, expected_band",
    [
        (0, "Low"),
        (29, "Low"),
        (30, "Medium"),
        (59, "Medium"),
        (60, "High"),
        (100, "High"),
    ],
)
def test_risk_band_boundaries(score, expected_band):
    assert risk_band(score) == expected_band


def test_combined_indicators_reach_score_cap():
    result = analyze_default(
        amount=8000,
        typical_amount=1000,
        is_new_beneficiary=True,
        transfers_in_10m=3,
        urgency_or_impersonation_reported=True,
    )

    assert result["raw_score"] == 100
    assert result["score"] == 100
    assert result["risk_band"] == "High"

    triggered_ids = [
        rule["rule_id"] for rule in result["triggered_rules"]
    ]

    assert triggered_ids == ["R-01", "R-03", "R-05", "R-06"]


def test_score_matches_triggered_rules_before_cap():
    result = analyze_default(
        amount=8000,
        typical_amount=1000,
        is_new_beneficiary=True,
        transfers_in_10m=3,
        urgency_or_impersonation_reported=True,
    )

    expected_raw_score = sum(
        rule["points"] for rule in result["triggered_rules"]
    )

    assert result["raw_score"] == expected_raw_score
    assert result["score"] == min(expected_raw_score, 100)


def test_rule_configuration_has_expected_points():
    expected_points = {
        "R-01": 20,
        "R-02": 15,
        "R-03": 30,
        "R-04": 15,
        "R-05": 25,
        "R-06": 25,
    }

    assert set(RULES) == set(expected_points)

    for rule_id, points in expected_points.items():
        assert RULES[rule_id]["points"] == points


def test_timestamp_window_includes_exact_boundary():
    target = datetime(2026, 1, 1, 12, 10, 0)
    timestamps = [
        target - timedelta(minutes=10),
        target - timedelta(minutes=5),
        target,
    ]

    assert count_transfers_in_window(
        timestamps, target_index=2, window_minutes=10
    ) == 3


def test_timestamp_window_excludes_event_just_before_boundary():
    target = datetime(2026, 1, 1, 12, 10, 0)
    timestamps = [
        target - timedelta(minutes=10, seconds=1),
        target - timedelta(minutes=5),
        target,
    ]

    assert count_transfers_in_window(
        timestamps, target_index=2, window_minutes=10
    ) == 2


def test_timestamp_window_excludes_events_after_target():
    target = datetime(2026, 1, 1, 12, 10, 0)
    timestamps = [
        target - timedelta(minutes=5),
        target,
        target + timedelta(seconds=1),
    ]

    assert count_transfers_in_window(
        timestamps, target_index=1, window_minutes=10
    ) == 2

@pytest.mark.parametrize("score", [-1, 101, True, 30.5, "60", None])
def test_risk_band_rejects_invalid_scores(score):
    with pytest.raises(ValueError):
        risk_band(score)

def test_raw_score_can_exceed_cap_but_display_score_is_100():
    result = analyze_transaction(
        amount=3000,
        typical_amount=1000,
        is_new_beneficiary=True,
        transfers_in_10m=3,
        urgency_or_impersonation_reported=True,
    )

    assert result["raw_score"] == 100
    assert result["score"] == 100
    assert result["risk_band"] == "High"


def test_triggered_rules_have_complete_explanations():
    result = analyze_transaction(
        amount=3000,
        typical_amount=1000,
        is_new_beneficiary=True,
        transfers_in_10m=3,
        urgency_or_impersonation_reported=True,
    )

    for rule in result["triggered_rules"]:
        assert rule["rule_id"]
        assert rule["name"]
        assert isinstance(rule["points"], int)
        assert rule["points"] > 0
        assert rule["evidence"].strip()

def test_timestamp_count_drives_velocity_rule():
    target = datetime(2026, 10, 10, 12, 10, 0)

    timestamps = [
        target - timedelta(minutes=9),
        target - timedelta(minutes=4),
        target,
    ]

    transfer_count = count_transfers_in_window(
        timestamps,
        target_index=2,
        window_minutes=10,
    )

    result = analyze_transaction(
        amount=1000,
        typical_amount=1000,
        is_new_beneficiary=False,
        transfers_in_10m=transfer_count,
        urgency_or_impersonation_reported=False,
    )

    assert transfer_count == 3
    assert result["score"] == 30
    assert result["risk_band"] == "Medium"
    assert [
        rule["rule_id"] for rule in result["triggered_rules"]
    ] == ["R-03"]
