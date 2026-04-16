from pathlib import Path

from core.benchmarks.runner import (
    RegressionThresholds,
    build_baseline_payload,
    build_payload,
    compare_with_baseline,
)


def test_compare_with_baseline_flags_time_regression():
    comparison = compare_with_baseline(
        baseline_entry={
            "wall_time_ms": 100.0,
            "query_count": 10,
            "db_time_ms": 50.0,
        },
        result={
            "status": "measured",
            "wall_time_ms": 130.0,
            "query_count": 10,
            "db_time_ms": 60.0,
        },
        thresholds=RegressionThresholds(
            time_regression_pct=20.0,
            time_regression_ms=25.0,
            query_regression=3,
        ),
    )

    assert comparison["status"] == "regression"
    assert comparison["time_regression"] is True
    assert comparison["query_regression"] is False


def test_compare_with_baseline_flags_query_regression():
    comparison = compare_with_baseline(
        baseline_entry={
            "wall_time_ms": 100.0,
            "query_count": 10,
            "db_time_ms": 50.0,
        },
        result={
            "status": "measured",
            "wall_time_ms": 101.0,
            "query_count": 14,
            "db_time_ms": 51.0,
        },
        thresholds=RegressionThresholds(
            time_regression_pct=20.0,
            time_regression_ms=25.0,
            query_regression=3,
        ),
    )

    assert comparison["status"] == "regression"
    assert comparison["time_regression"] is False
    assert comparison["query_regression"] is True


def test_compare_with_baseline_ignores_small_absolute_time_noise():
    comparison = compare_with_baseline(
        baseline_entry={
            "wall_time_ms": 10.0,
            "query_count": 10,
            "db_time_ms": 5.0,
        },
        result={
            "status": "measured",
            "wall_time_ms": 14.0,
            "query_count": 10,
            "db_time_ms": 5.0,
        },
        thresholds=RegressionThresholds(
            time_regression_pct=20.0,
            time_regression_ms=25.0,
            query_regression=3,
        ),
    )

    assert comparison["status"] == "ok"
    assert comparison["time_regression"] is False
    assert comparison["query_regression"] is False


def test_build_payload_and_baseline_only_include_measured_results():
    payload = build_payload(
        results=[
            {
                "scenario_id": "core:programas",
                "module": "core",
                "label": "Listado de programas",
                "status": "measured",
                "wall_time_ms": 10.0,
                "query_count": 2,
                "db_time_ms": 5.0,
                "status_code": 200,
                "comparison": {"status": "ok"},
            },
            {
                "scenario_id": "vat:list",
                "module": "VAT",
                "label": "Listado VAT",
                "status": "skipped",
                "reason": "sin seed",
                "comparison": {"status": "not-compared"},
            },
        ],
        thresholds=RegressionThresholds(),
        samples=5,
        warmups=1,
        baseline_path=Path("benchmarks/baselines/default.json"),
    )

    baseline = build_baseline_payload(payload)

    assert payload["summary"]["measured"] == 1
    assert payload["summary"]["skipped"] == 1
    assert "core:programas" in baseline["scenarios"]
    assert "vat:list" not in baseline["scenarios"]
