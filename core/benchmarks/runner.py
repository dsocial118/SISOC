"""Runner y comparación de benchmarks reproducibles."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
from django.test import Client
from django.urls import reverse

from core.benchmarks.bootstrap import BenchmarkSeedState
from core.benchmarks.scenarios import BenchmarkScenario, ScenarioSkip


@dataclass(frozen=True)
class RegressionThresholds:
    """Umbrales usados para detectar regresiones."""

    time_regression_pct: float = 20.0
    time_regression_ms: float = 25.0
    query_regression: int = 3


@dataclass
class SampleMeasurement:
    """Métricas crudas de una ejecución individual."""

    wall_time_ms: float
    query_count: int
    db_time_ms: float
    status_code: int


class BenchmarkRunner:
    """Ejecuta escenarios, serializa artefactos y detecta regresiones."""

    def __init__(
        self,
        *,
        scenarios: list[BenchmarkScenario],
        seed_state: BenchmarkSeedState,
        thresholds: RegressionThresholds,
        samples: int = 5,
        warmups: int = 1,
    ) -> None:
        self.scenarios = scenarios
        self.seed_state = seed_state
        self.thresholds = thresholds
        self.samples = samples
        self.warmups = warmups

    def run(
        self,
        *,
        baseline_path: Path,
        output_path: Path,
        rebuild_baseline: bool = False,
    ) -> dict[str, Any]:
        """Ejecuta los escenarios y deja resultados serializados."""
        baseline_data = load_baseline(baseline_path)
        client = Client()
        benchmark_user = get_user_model().objects.get(
            username=self.seed_state.benchmark_username
        )

        results: list[dict[str, Any]] = []
        for scenario in self.scenarios:
            result = self._run_scenario(client, benchmark_user, scenario)
            baseline_entry = baseline_data.get("scenarios", {}).get(scenario.scenario_id)
            result["comparison"] = compare_with_baseline(
                baseline_entry=baseline_entry,
                result=result,
                thresholds=self.thresholds,
            )
            results.append(result)

        payload = build_payload(
            results=results,
            thresholds=self.thresholds,
            samples=self.samples,
            warmups=self.warmups,
            baseline_path=baseline_path,
        )
        write_json(output_path, payload)

        if rebuild_baseline:
            baseline_payload = build_baseline_payload(payload)
            write_json(baseline_path, baseline_payload)

        return payload

    def _run_scenario(
        self,
        client: Client,
        benchmark_user,
        scenario: BenchmarkScenario,
    ) -> dict[str, Any]:
        """Ejecuta un escenario con warmup y muestras medidas."""
        try:
            if scenario.requires_auth:
                client.force_login(benchmark_user)
            else:
                client.logout()

            for _ in range(self.warmups):
                self._execute_once(client, scenario)

            samples = [self._execute_once(client, scenario) for _ in range(self.samples)]
            return serialize_measured_scenario(scenario, samples)
        except ScenarioSkip as exc:
            return {
                "scenario_id": scenario.scenario_id,
                "module": scenario.module,
                "label": scenario.label,
                "status": "skipped",
                "reason": str(exc),
            }
        except Exception as exc:  # pragma: no cover - defensivo para el runner
            return {
                "scenario_id": scenario.scenario_id,
                "module": scenario.module,
                "label": scenario.label,
                "status": "failed",
                "reason": str(exc),
            }

    def _execute_once(
        self,
        client: Client,
        scenario: BenchmarkScenario,
    ) -> SampleMeasurement:
        """Ejecuta una sola medición de un escenario."""
        connection.force_debug_cursor = True
        reset_queries()

        try:
            start = time.perf_counter()
            if scenario.route_name:
                kwargs = (
                    scenario.kwargs_factory(self.seed_state)
                    if scenario.kwargs_factory
                    else {}
                )
                path = reverse(scenario.route_name, kwargs=kwargs)
                response = getattr(client, scenario.method.lower())(path)
                status_code = response.status_code
                if status_code not in scenario.expected_statuses:
                    raise RuntimeError(
                        f"{scenario.scenario_id} devolvió {status_code} en {path}"
                    )
            elif scenario.callable_runner:
                scenario.callable_runner(self.seed_state)
                status_code = 200
            else:  # pragma: no cover - contrato inválido
                raise RuntimeError(f"Escenario inválido: {scenario.scenario_id}")
            elapsed_ms = (time.perf_counter() - start) * 1000

            db_time_ms = (
                sum(float(query["time"]) for query in connection.queries) * 1000
            )
            return SampleMeasurement(
                wall_time_ms=elapsed_ms,
                query_count=len(connection.queries),
                db_time_ms=db_time_ms,
                status_code=status_code,
            )
        finally:
            connection.force_debug_cursor = False


def serialize_measured_scenario(
    scenario: BenchmarkScenario,
    samples: list[SampleMeasurement],
) -> dict[str, Any]:
    """Resume una batería de muestras en una medición comparable."""
    wall_times = [sample.wall_time_ms for sample in samples]
    query_counts = [sample.query_count for sample in samples]
    db_times = [sample.db_time_ms for sample in samples]
    status_codes = [sample.status_code for sample in samples]

    return {
        "scenario_id": scenario.scenario_id,
        "module": scenario.module,
        "label": scenario.label,
        "status": "measured",
        "wall_time_ms": round(statistics.median(wall_times), 2),
        "query_count": int(round(statistics.median(query_counts))),
        "db_time_ms": round(statistics.median(db_times), 2),
        "status_code": int(round(statistics.median(status_codes))),
        "samples": [asdict(sample) for sample in samples],
    }


def compare_with_baseline(
    *,
    baseline_entry: dict[str, Any] | None,
    result: dict[str, Any],
    thresholds: RegressionThresholds,
) -> dict[str, Any]:
    """Compara una medición con su baseline y marca regresiones."""
    if result["status"] != "measured":
        return {"status": "not-compared"}

    if not baseline_entry:
        return {"status": "new"}

    time_delta_ms = round(result["wall_time_ms"] - baseline_entry["wall_time_ms"], 2)
    base_time = float(baseline_entry["wall_time_ms"] or 0)
    time_delta_pct = round((time_delta_ms / base_time) * 100, 2) if base_time else 0.0
    query_delta = int(result["query_count"] - baseline_entry["query_count"])
    db_time_delta_ms = round(result["db_time_ms"] - baseline_entry["db_time_ms"], 2)

    pct_threshold_exceeded = (
        time_delta_pct >= thresholds.time_regression_pct if base_time else True
    )
    time_regression = (
        time_delta_ms > 0
        and time_delta_ms >= thresholds.time_regression_ms
        and pct_threshold_exceeded
    )
    query_regression = query_delta >= thresholds.query_regression

    status = "regression" if (time_regression or query_regression) else "ok"
    return {
        "status": status,
        "time_delta_ms": time_delta_ms,
        "time_delta_pct": time_delta_pct,
        "query_delta": query_delta,
        "db_time_delta_ms": db_time_delta_ms,
        "time_regression": time_regression,
        "query_regression": query_regression,
    }


def build_payload(
    *,
    results: list[dict[str, Any]],
    thresholds: RegressionThresholds,
    samples: int,
    warmups: int,
    baseline_path: Path,
) -> dict[str, Any]:
    """Compone el artefacto final de la corrida."""
    measured = [result for result in results if result["status"] == "measured"]
    skipped = [result for result in results if result["status"] == "skipped"]
    failed = [result for result in results if result["status"] == "failed"]
    regressions = [
        result
        for result in measured
        if result["comparison"]["status"] == "regression"
    ]

    modules: dict[str, dict[str, Any]] = {}
    for result in results:
        module_entry = modules.setdefault(
            result["module"],
            {"module": result["module"], "measured": 0, "skipped": 0, "failed": 0},
        )
        module_entry[result["status"]] = module_entry.get(result["status"], 0) + 1

    return {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "samples": samples,
            "warmups": warmups,
            "baseline_path": str(baseline_path),
            "thresholds": asdict(thresholds),
        },
        "summary": {
            "measured": len(measured),
            "skipped": len(skipped),
            "failed": len(failed),
            "regressions": len(regressions),
        },
        "modules": sorted(modules.values(), key=lambda item: item["module"]),
        "results": results,
    }


def build_baseline_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Extrae una versión compacta y versionable del baseline."""
    measured = {
        result["scenario_id"]: {
            "module": result["module"],
            "label": result["label"],
            "wall_time_ms": result["wall_time_ms"],
            "query_count": result["query_count"],
            "db_time_ms": result["db_time_ms"],
            "status_code": result["status_code"],
        }
        for result in payload["results"]
        if result["status"] == "measured"
    }
    return {
        "meta": payload["meta"],
        "scenarios": measured,
    }


def load_baseline(path: Path) -> dict[str, Any]:
    """Lee baseline si existe; si no, devuelve estructura vacía."""
    if not path.exists():
        return {"scenarios": {}}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Escribe un JSON con directorio padre garantizado."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
