"""Management command para benchmarks reproducibles de performance."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.benchmarks.bootstrap import (
    build_seed_state,
    close_connections,
    default_baseline_path,
    default_output_path,
)
from core.benchmarks.runner import BenchmarkRunner, RegressionThresholds
from core.benchmarks.scenarios import all_scenarios


class Command(BaseCommand):
    help = (
        "Ejecuta benchmarks reproducibles en una DB efímera y compara contra "
        "un baseline versionado."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--module",
            action="append",
            dest="modules",
            help="Filtra módulos específicos (se puede repetir).",
        )
        parser.add_argument(
            "--scenario",
            action="append",
            dest="scenario_ids",
            help="Filtra escenarios por id (se puede repetir).",
        )
        parser.add_argument(
            "--samples",
            type=int,
            default=5,
            help="Cantidad de muestras medidas por escenario.",
        )
        parser.add_argument(
            "--warmups",
            type=int,
            default=1,
            help="Cantidad de warmups no medidos por escenario.",
        )
        parser.add_argument(
            "--baseline",
            default=str(default_baseline_path()),
            help="Ruta del baseline JSON versionado.",
        )
        parser.add_argument(
            "--output",
            default=str(default_output_path()),
            help="Ruta del resultado JSON de la corrida.",
        )
        parser.add_argument(
            "--rebuild-baseline",
            action="store_true",
            help="Reemplaza el baseline actual con la corrida medida.",
        )
        parser.add_argument(
            "--time-threshold-pct",
            type=float,
            default=20.0,
            help="Umbral porcentual de regresión de tiempo.",
        )
        parser.add_argument(
            "--time-threshold-ms",
            type=float,
            default=25.0,
            help="Umbral absoluto de regresión de tiempo en milisegundos.",
        )
        parser.add_argument(
            "--query-threshold",
            type=int,
            default=3,
            help="Umbral de regresión por cantidad de queries.",
        )
        parser.add_argument(
            "--internal",
            action="store_true",
            help="Marca la ejecución interna sobre DB efímera.",
        )

    def handle(self, *args, **options):
        if not options["internal"]:
            return self._run_in_ephemeral_subprocess(options)
        return self._run_internal(options)

    def _run_in_ephemeral_subprocess(self, options):
        command = [
            sys.executable,
            "manage.py",
            "run_benchmarks",
            "--internal",
            "--samples",
            str(options["samples"]),
            "--warmups",
            str(options["warmups"]),
            "--baseline",
            options["baseline"],
            "--output",
            options["output"],
            "--time-threshold-pct",
            str(options["time_threshold_pct"]),
            "--time-threshold-ms",
            str(options["time_threshold_ms"]),
            "--query-threshold",
            str(options["query_threshold"]),
        ]
        for module in options["modules"] or []:
            command.extend(["--module", module])
        for scenario_id in options["scenario_ids"] or []:
            command.extend(["--scenario", scenario_id])
        if options["rebuild_baseline"]:
            command.append("--rebuild-baseline")

        env = os.environ.copy()
        env["PYTEST_RUNNING"] = "1"
        env["USE_SQLITE_FOR_TESTS"] = "1"
        env["DJANGO_DEBUG"] = "True"
        completed = subprocess.run(command, env=env, check=False)
        if completed.returncode != 0:
            raise CommandError(
                "La corrida interna de benchmarks falló con código "
                f"{completed.returncode}."
            )

    def _run_internal(self, options):
        baseline_path = Path(options["baseline"])
        output_path = Path(options["output"])
        thresholds = RegressionThresholds(
            time_regression_pct=options["time_threshold_pct"],
            time_regression_ms=options["time_threshold_ms"],
            query_regression=options["query_threshold"],
        )

        scenarios = [
            scenario
            for scenario in all_scenarios()
            if (
                (not options["modules"] or scenario.module in options["modules"])
                and (
                    not options["scenario_ids"]
                    or scenario.scenario_id in options["scenario_ids"]
                )
            )
        ]
        if not scenarios:
            raise CommandError("No quedaron escenarios luego de aplicar filtros.")

        self.stdout.write("Preparando DB efímera y datos reproducibles...")
        seed_state = build_seed_state()
        runner = BenchmarkRunner(
            scenarios=scenarios,
            seed_state=seed_state,
            thresholds=thresholds,
            samples=options["samples"],
            warmups=options["warmups"],
        )
        payload = runner.run(
            baseline_path=baseline_path,
            output_path=output_path,
            rebuild_baseline=options["rebuild_baseline"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Benchmarks completados: "
                f"medidos={payload['summary']['measured']} "
                f"skipped={payload['summary']['skipped']} "
                f"failed={payload['summary']['failed']} "
                f"regressions={payload['summary']['regressions']}"
            )
        )
        self.stdout.write(f"Resultado JSON: {output_path}")
        if options["rebuild_baseline"]:
            self.stdout.write(f"Baseline actualizado: {baseline_path}")

        close_connections()

        if payload["summary"]["failed"] or payload["summary"]["regressions"]:
            raise CommandError(
                "Se detectaron fallos o regresiones. Revisá el JSON generado."
            )
