from datetime import datetime, timedelta
import math

import pandas as pd

import pytest

from detector import analyze_transaction
from scenarios import SCENARIOS, build_scenario


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_every_scenario_builds_expected_columns(scenario_name):
    df = build_scenario(scenario_name, typical_amount=1000)

    assert not df.empty
    assert {
        "time",
        "amount_inr",
        "beneficiary_label",
        "is_new_beneficiary",
        "transfers_in_10m",
        "urgency_or_impersonation_reported",
        "scenario",
        "typical_amount",
    }.issubset(df.columns)

    assert (df["amount_inr"] > 0).all()
    assert (df["typical_amount"] == 1000).all()
    assert (df["scenario"] == scenario_name).all()


@pytest.mark.parametrize(
    ("scenario_name", "expected_counts"),
    [
        ("Normal activity", [1, 1, 1, 1]),
        ("New beneficiary", [1]),
        ("Rapid transfers to a new beneficiary", [1, 2, 3]),
        ("Urgency / impersonation indicators", [1, 2]),
        ("Unusual amount", [1]),
        ("Combined warning indicators", [1, 2, 3]),
    ],
)
def test_scenario_transfer_counts(scenario_name, expected_counts):
    df = build_scenario(scenario_name, typical_amount=1000)

    assert df["transfers_in_10m"].tolist() == expected_counts


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_scenario_counts_match_timestamps(scenario_name):
    df = build_scenario(scenario_name, typical_amount=1000)
    timestamps = df["time"].tolist()

    for index, target_time in enumerate(timestamps):
        window_start = target_time - timedelta(minutes=10)

        expected_count = sum(
            1
            for timestamp in timestamps
            if window_start <= timestamp <= target_time
        )

        assert df.iloc[index]["transfers_in_10m"] == expected_count


@pytest.mark.parametrize("scenario_name", list(SCENARIOS.keys()))
def test_every_scenario_produces_valid_detector_results(scenario_name):
    df = build_scenario(scenario_name, typical_amount=1000)

    for _, row in df.iterrows():
        result = analyze_transaction(
            amount=float(row["amount_inr"]),
            typical_amount=float(row["typical_amount"]),
            is_new_beneficiary=bool(row["is_new_beneficiary"]),
            transfers_in_10m=int(row["transfers_in_10m"]),
            urgency_or_impersonation_reported=bool(
                row["urgency_or_impersonation_reported"]
            ),
        )

        points_sum = sum(
            rule["points"] for rule in result["triggered_rules"]
        )

        assert result["score"] == min(points_sum, 100)
        assert result["risk_band"] in {"Low", "Medium", "High"}
        assert 0 <= result["score"] <= 100


def test_unknown_scenario_is_rejected():
    with pytest.raises(ValueError):
        build_scenario("Not a real scenario", typical_amount=1000)


@pytest.mark.parametrize("invalid_amount", [0, -1, True, float("inf"), float("nan")])
def test_invalid_typical_amount_is_rejected(invalid_amount):
    with pytest.raises(ValueError):
        build_scenario("Normal activity", typical_amount=invalid_amount)
