"""Catálogo de escenarios de benchmark para módulos SISOC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Callable
from unittest import mock

from django.apps import apps
from django.contrib.auth import get_user_model

from core.benchmarks.bootstrap import BenchmarkSeedState


class ScenarioSkip(Exception):
    """Señala que un escenario no puede medirse con el dataset actual."""


@dataclass(frozen=True)
class BenchmarkScenario:
    """Describe un escenario medible por URL o callable."""

    scenario_id: str
    module: str
    label: str
    route_name: str | None = None
    method: str = "GET"
    kwargs_factory: Callable[[BenchmarkSeedState], dict[str, Any]] | None = None
    callable_runner: Callable[[BenchmarkSeedState], None] | None = None
    requires_auth: bool = True
    expected_statuses: tuple[int, ...] = (200,)


def seeded_pk(
    seed_state: BenchmarkSeedState,
    key: str,
    kwarg: str = "pk",
) -> dict[str, int]:
    """Devuelve kwargs basados en IDs sembrados o marca skip."""
    value = seed_state.get_id(key)
    if value is None:
        raise ScenarioSkip(f"Falta semilla para '{key}'")
    return {kwarg: value}


def all_scenarios() -> list[BenchmarkScenario]:
    """Devuelve la matriz base de escenarios profundos por módulo."""
    return [
        BenchmarkScenario("users:list", "users", "Listado de usuarios", "usuarios"),
        BenchmarkScenario("users:groups", "users", "Listado de grupos", "grupos"),
        BenchmarkScenario("core:inicio", "core", "Inicio", "inicio"),
        BenchmarkScenario(
            "core:programas", "core", "Listado de programas", "programa_listar"
        ),
        BenchmarkScenario(
            "core:montos",
            "core",
            "Listado de montos de prestación",
            "montoprestacion_listar",
        ),
        BenchmarkScenario(
            "dashboard:list", "dashboard", "Dashboard principal", "dashboard"
        ),
        BenchmarkScenario(
            "dashboard:tablero",
            "dashboard",
            "Detalle de tablero",
            "dashboard_tablero",
            kwargs_factory=lambda seed: {"slug": "tablero-benchmark"},
        ),
        BenchmarkScenario(
            "comedores:list", "comedores", "Listado de comedores", "comedores"
        ),
        BenchmarkScenario(
            "comedores:detail",
            "comedores",
            "Detalle de comedor",
            "comedor_detalle",
            kwargs_factory=lambda seed: seeded_pk(seed, "comedor"),
        ),
        BenchmarkScenario(
            "organizaciones:list",
            "organizaciones",
            "Listado de organizaciones",
            "organizaciones",
        ),
        BenchmarkScenario("duplas:list", "duplas", "Listado de duplas", "dupla_list"),
        BenchmarkScenario(
            "audittrail:list",
            "audittrail",
            "Listado de auditoría",
            "audittrail:log_list",
        ),
        BenchmarkScenario(
            "ciudadanos:list",
            "ciudadanos",
            "Listado de ciudadanos",
            "ciudadanos",
        ),
        BenchmarkScenario(
            "ciudadanos:detail",
            "ciudadanos",
            "Detalle de ciudadano",
            "ciudadanos_ver",
            kwargs_factory=lambda seed: seeded_pk(seed, "ciudadano"),
        ),
        BenchmarkScenario(
            "admisiones:tecnicos",
            "admisiones",
            "Listado de admisiones técnicas",
            "admisiones_tecnicos_listar",
        ),
        BenchmarkScenario(
            "admisiones:legales",
            "admisiones",
            "Listado de admisiones legales",
            "admisiones_legales_listar",
        ),
        BenchmarkScenario(
            "intervenciones:create",
            "intervenciones",
            "Formulario de intervención",
            "comedor_intervencion_crear",
            kwargs_factory=lambda seed: seeded_pk(seed, "comedor"),
        ),
        BenchmarkScenario(
            "centrodefamilia:list",
            "centrodefamilia",
            "Listado de centros de familia",
            "centro_list",
        ),
        BenchmarkScenario("VAT:list", "VAT", "Listado de centros VAT", "vat_centro_list"),
        BenchmarkScenario(
            "centrodeinfancia:list",
            "centrodeinfancia",
            "Listado de CDI",
            "centrodeinfancia",
        ),
        BenchmarkScenario(
            "centrodeinfancia:formularios",
            "centrodeinfancia",
            "Listado de formularios CDI",
            "centrodeinfancia_formulario_listado",
            kwargs_factory=lambda seed: seeded_pk(seed, "centrodeinfancia"),
        ),
        BenchmarkScenario(
            "acompanamientos:list",
            "acompanamientos",
            "Listado de acompañamientos",
            "lista_comedores_acompanamiento",
        ),
        BenchmarkScenario(
            "expedientespagos:list",
            "expedientespagos",
            "Listado de expedientes de pago",
            "expedientespagos_list",
            kwargs_factory=lambda seed: seeded_pk(seed, "comedor"),
        ),
        BenchmarkScenario(
            "relevamientos:list",
            "relevamientos",
            "Listado de relevamientos",
            "relevamientos",
            kwargs_factory=lambda seed: seeded_pk(seed, "comedor", "comedor_pk"),
        ),
        BenchmarkScenario(
            "rendicioncuentasfinal:list",
            "rendicioncuentasfinal",
            "Listado de rendiciones finales",
            "rendicion_cuentas_final_listar",
        ),
        BenchmarkScenario(
            "rendicioncuentasmensual:list",
            "rendicioncuentasmensual",
            "Listado global de rendiciones mensuales",
            "rendicioncuentasmensual_global_list",
        ),
        BenchmarkScenario(
            "celiaquia:list",
            "celiaquia",
            "Listado de expedientes celiaquía",
            "expediente_list",
        ),
        BenchmarkScenario(
            "celiaquia:detail",
            "celiaquia",
            "Detalle de expediente celiaquía",
            "expediente_detail",
            kwargs_factory=lambda seed: seeded_pk(seed, "expediente"),
        ),
        BenchmarkScenario(
            "importarexpediente:list",
            "importarexpediente",
            "Listado de importación de expedientes",
            "importarexpedientes_list",
        ),
        BenchmarkScenario(
            "comunicados:list",
            "comunicados",
            "Listado público de comunicados",
            "comunicados",
        ),
        BenchmarkScenario(
            "comunicados:gestion",
            "comunicados",
            "Listado de gestión de comunicados",
            "comunicados_gestion",
        ),
        BenchmarkScenario(
            "comunicados:detail",
            "comunicados",
            "Detalle de comunicado",
            "comunicados_ver",
            kwargs_factory=lambda seed: seeded_pk(seed, "comunicado"),
        ),
        BenchmarkScenario(
            "pwa:health",
            "pwa",
            "Healthcheck API PWA",
            "pwa-health-list",
            requires_auth=False,
        ),
        BenchmarkScenario(
            "historial:service",
            "historial",
            "Registro de historial serializado",
            callable_runner=run_historial_service_benchmark,
        ),
    ]


def run_historial_service_benchmark(seed_state: BenchmarkSeedState) -> None:
    """Ejecuta un escenario callable para el módulo historial."""
    historial_model = apps.get_model("historial", "Historial")
    historial_model.objects.all().delete()

    user_model = get_user_model()
    benchmark_user = user_model.objects.get(username=seed_state.benchmark_username)
    programa_model = apps.get_model("core", "Programa")
    monto_model = apps.get_model("core", "MontoPrestacionPrograma")
    programa = programa_model.objects.get(pk=seed_state.get_id("programa"))

    monto = monto_model.objects.create(
        programa=programa,
        desayuno_valor=Decimal("10.50"),
        almuerzo_valor=Decimal("20.75"),
        merienda_valor=Decimal("5.25"),
        cena_valor=Decimal("15.00"),
        usuario_creador=benchmark_user,
    )

    payload = {
        "decimal": Decimal("12.34"),
        "date": date(2025, 1, 2),
        "list": [Decimal("1.23"), date(2025, 1, 4)],
        "queryset": programa_model.objects.filter(pk=programa.pk),
        "model": programa,
        "none": None,
    }

    from historial.services.historial_service import HistorialService

    with mock.patch(
        "config.middlewares.threadlocals.get_current_user",
        return_value=benchmark_user,
    ):
        HistorialService.registrar_historial(
            accion="Benchmark",
            instancia=monto,
            diferencias=payload,
        )
