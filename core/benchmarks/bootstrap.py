"""Bootstrap reproducible para benchmarks de performance."""

from __future__ import annotations

from io import StringIO
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import re

from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test.utils import get_runner
from django.utils import timezone

_test_runner = None
_db_config = None


@dataclass
class BenchmarkSeedState:
    """Estado mínimo generado para destrabar escenarios reproducibles."""

    benchmark_username: str = "benchmark-admin"
    object_ids: dict[str, int] = field(default_factory=dict)

    def set_id(self, key: str, value: int | None) -> None:
        """Guarda un identificador si el objeto existe."""
        if value is not None:
            self.object_ids[key] = value

    def get_id(self, key: str) -> int | None:
        """Obtiene un identificador previamente sembrado."""
        return self.object_ids.get(key)


def ensure_benchmark_database() -> None:
    """Crea el schema efímero que usará el benchmark."""
    global _test_runner, _db_config

    # En la corrida interna usamos infraestructura de tests de Django para
    # respetar `TEST["MIGRATE"] = False` y evitar migraciones incompatibles con
    # SQLite en memoria.
    if _test_runner is None:
        runner_class = get_runner(settings)
        _test_runner = runner_class(verbosity=0, interactive=False, keepdb=False)
        _test_runner.setup_test_environment()
        _db_config = _test_runner.setup_databases()

    call_command("create_groups", verbosity=0)
    call_command("sync_group_permissions_from_registry", verbosity=0)
    load_benchmark_fixtures()


def build_seed_state() -> BenchmarkSeedState:
    """Carga fixtures y crea datos mínimos para benchmarks transversales."""
    ensure_benchmark_database()

    state = BenchmarkSeedState()
    benchmark_user = ensure_benchmark_superuser(state.benchmark_username)
    state.set_id("benchmark_user", benchmark_user.pk)

    provincia = ensure_provincia()
    programa = ensure_programa(benchmark_user)
    dupla = ensure_dupla()
    comedor = ensure_comedor(programa, provincia, dupla)
    ciudadano = ensure_ciudadano()
    organizacion = ensure_organizacion()
    tablero = ensure_tablero()
    centro_infancia = ensure_centro_de_infancia(provincia)
    comunicado = ensure_comunicado(benchmark_user)
    expediente = ensure_celiaquia_expediente(provincia)

    state.set_id("provincia", getattr(provincia, "pk", None))
    state.set_id("programa", getattr(programa, "pk", None))
    state.set_id("dupla", getattr(dupla, "pk", None))
    state.set_id("comedor", getattr(comedor, "pk", None))
    state.set_id("ciudadano", getattr(ciudadano, "pk", None))
    state.set_id("organizacion", getattr(organizacion, "pk", None))
    state.set_id("tablero", getattr(tablero, "pk", None))
    state.set_id("centrodeinfancia", getattr(centro_infancia, "pk", None))
    state.set_id("comunicado", getattr(comunicado, "pk", None))
    state.set_id("expediente", getattr(expediente, "pk", None))

    return state


def ensure_benchmark_superuser(username: str):
    """Crea el usuario administrador usado por el runner."""
    user_model = get_user_model()
    user, created = user_model.objects.get_or_create(
        username=username,
        defaults={
            "email": "benchmark@sisoc.local",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created or not user.check_password("benchmark-pass"):
        user.is_staff = True
        user.is_superuser = True
        user.email = user.email or "benchmark@sisoc.local"
        user.set_password("benchmark-pass")
        user.save()
    return user_model.objects.get(pk=user.pk)


def ensure_provincia():
    """Recupera o crea una provincia para datos mínimos de benchmark."""
    provincia_model = apps.get_model("core", "Provincia")
    provincia = provincia_model.objects.order_by("pk").first()
    if provincia:
        return provincia
    return provincia_model.objects.create(nombre="Provincia Benchmark")


def ensure_programa(benchmark_user):
    """Asegura un programa base para escenarios transversales."""
    programa_model = apps.get_model("core", "Programa")
    programa = programa_model.objects.order_by("pk").first()
    if programa:
        return programa

    programa = programa_model.objects.create(nombre="Programa Benchmark")

    monto_model = apps.get_model("core", "MontoPrestacionPrograma")
    if not monto_model.objects.filter(programa=programa).exists():
        monto_model.objects.create(
            programa=programa,
            desayuno_valor=10,
            almuerzo_valor=20,
            merienda_valor=8,
            cena_valor=15,
            usuario_creador=benchmark_user,
        )
    return programa


def ensure_dupla():
    """Asegura una dupla mínima para módulos de comedores."""
    dupla_model = apps.get_model("duplas", "Dupla")
    dupla = dupla_model.objects.order_by("pk").first()
    if dupla:
        return dupla

    abogado = ensure_staff_user(
        username="benchmark-abogado",
        email="benchmark-abogado@sisoc.local",
        first_name="Alicia",
        last_name="Benchmark",
    )
    tecnico = ensure_staff_user(
        username="benchmark-tecnico",
        email="benchmark-tecnico@sisoc.local",
        first_name="Tomas",
        last_name="Benchmark",
    )

    dupla = dupla_model.objects.create(
        nombre="Dupla Benchmark",
        estado="Activo",
        abogado=abogado,
    )
    dupla.tecnico.add(tecnico)
    return dupla


def ensure_staff_user(
    *,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
):
    """Crea usuarios simples reutilizables para seeds relacionados."""
    user_model = get_user_model()
    user, _ = user_model.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_staff": True,
        },
    )
    dirty = False
    if user.email != email:
        user.email = email
        dirty = True
    if user.first_name != first_name:
        user.first_name = first_name
        dirty = True
    if user.last_name != last_name:
        user.last_name = last_name
        dirty = True
    if not user.is_staff:
        user.is_staff = True
        dirty = True
    if not user.check_password("benchmark-pass"):
        user.set_password("benchmark-pass")
        dirty = True
    if dirty:
        user.save()
    return user_model.objects.get(pk=user.pk)


def ensure_comedor(_programa, provincia, dupla):
    """Asegura un comedor mínimo para módulos dependientes."""
    comedor_model = apps.get_model("comedores", "Comedor")
    comedor = comedor_model.objects.order_by("pk").first()
    if comedor:
        return comedor

    programa_comedor = ensure_comedor_programa()
    kwargs = {"nombre": "Comedor Benchmark"}
    if has_field(comedor_model, "programa") and programa_comedor is not None:
        kwargs["programa"] = programa_comedor
    if has_field(comedor_model, "provincia") and provincia is not None:
        kwargs["provincia"] = provincia
    if has_field(comedor_model, "dupla") and dupla is not None:
        kwargs["dupla"] = dupla
    return comedor_model.objects.create(**kwargs)


def ensure_comedor_programa():
    """Recupera el catálogo de programas propio de comedores."""
    programa_model = apps.get_model("comedores", "Programas")
    programa = programa_model.objects.order_by("pk").first()
    if programa:
        return programa
    return programa_model.objects.create(nombre="Programa comedor benchmark")


def ensure_ciudadano():
    """Asegura un ciudadano para módulos de listados/detalles."""
    ciudadano_model = apps.get_model("ciudadanos", "Ciudadano")
    ciudadano = ciudadano_model.objects.order_by("pk").first()
    if ciudadano:
        return ciudadano
    return ciudadano_model.objects.create(
        apellido="Benchmark",
        nombre="Ciudadano",
        fecha_nacimiento=date(1990, 1, 1),
        documento=34567890,
    )


def ensure_organizacion():
    """Asegura una organización para escenarios básicos."""
    organizacion_model = apps.get_model("organizaciones", "Organizacion")
    organizacion = organizacion_model.objects.order_by("pk").first()
    if organizacion:
        return organizacion
    return organizacion_model.objects.create(nombre="Organización Benchmark")


def ensure_tablero():
    """Asegura un tablero mínimo para el módulo dashboard."""
    tablero_model = apps.get_model("dashboard", "Tablero")
    tablero = tablero_model.objects.filter(slug="tablero-benchmark").first()
    if tablero:
        return tablero
    return tablero_model.objects.create(
        nombre="Tablero Benchmark",
        slug="tablero-benchmark",
        url="https://lookerstudio.google.com/reporting/benchmark",
        activo=True,
        permisos=["dashboard.view_dashboard"],
    )


def ensure_centro_de_infancia(provincia):
    """Asegura un CDI mínimo para benchmarks del módulo."""
    centro_model = apps.get_model("centrodeinfancia", "CentroDeInfancia")
    centro = centro_model.objects.order_by("pk").first()
    if centro:
        return centro

    kwargs = {"nombre": "CDI Benchmark"}
    if has_field(centro_model, "provincia") and provincia is not None:
        kwargs["provincia"] = provincia
    if has_field(centro_model, "codigo_cdi"):
        kwargs["codigo_cdi"] = "CDI-BENCH-001"
    return centro_model.objects.create(**kwargs)


def ensure_comunicado(benchmark_user):
    """Asegura un comunicado publicado para vistas públicas/detalle."""
    comunicado_model = apps.get_model("comunicados", "Comunicado")
    comunicado = comunicado_model.objects.order_by("pk").first()
    if comunicado:
        return comunicado

    from comunicados.models import EstadoComunicado, TipoComunicado

    return comunicado_model.objects.create(
        titulo="Comunicado Benchmark",
        cuerpo="Contenido de benchmark",
        estado=EstadoComunicado.PUBLICADO,
        tipo=TipoComunicado.INTERNO,
        fecha_publicacion=timezone.now(),
        usuario_creador=benchmark_user,
    )


def ensure_celiaquia_expediente(provincia):
    """Asegura un expediente mínimo para el módulo de celiaquía."""
    expediente_model = apps.get_model("celiaquia", "Expediente")
    expediente = expediente_model.objects.order_by("pk").first()
    if expediente:
        return expediente

    estado_model = apps.get_model("celiaquia", "EstadoExpediente")
    estado, _ = estado_model.objects.get_or_create(nombre="BENCHMARK")

    user_model = get_user_model()
    usuario, _ = user_model.objects.get_or_create(
        username="benchmark-celiaquia",
        defaults={"email": "celiaquia@sisoc.local"},
    )
    if not usuario.check_password("benchmark-pass"):
        usuario.set_password("benchmark-pass")
        usuario.save()

    profile_model = apps.get_model("users", "Profile")
    profile, _ = profile_model.objects.get_or_create(user=usuario)
    if has_field(profile_model, "es_usuario_provincial"):
        profile.es_usuario_provincial = True
    if has_field(profile_model, "provincia"):
        profile.provincia = provincia
    profile.save()

    return expediente_model.objects.create(usuario_provincia=usuario, estado=estado)


def load_benchmark_fixtures() -> None:
    """Carga fixtures y resume incidencias conocidas para la corrida efímera."""
    stdout = StringIO()
    stderr = StringIO()
    call_command("load_fixtures", force=True, verbosity=0, stdout=stdout, stderr=stderr)

    loaded_fixtures = 0
    fixture_failures: list[str] = []
    for line in stdout.getvalue().splitlines():
        if "created=" not in line or "failed=" not in line:
            continue
        loaded_fixtures += 1
        match = re.search(r"(?P<path>.+?): .*failed=(?P<failed>\d+)", line)
        if match and int(match.group("failed")) > 0:
            fixture_failures.append(
                f"{match.group('path').strip()}: {match.group('failed')} registros omitidos"
            )

    if loaded_fixtures:
        print(f"Fixtures benchmark cargados: {loaded_fixtures} archivos procesados.")
    if fixture_failures:
        print(
            "Fixtures con incidencias toleradas en SQLite de benchmark: "
            + "; ".join(fixture_failures)
        )


def has_field(model, field_name: str) -> bool:
    """Indica si un modelo expone un campo concreto."""
    return any(field.name == field_name for field in model._meta.get_fields())


def default_baseline_path() -> Path:
    """Devuelve la ubicación default del baseline versionado."""
    return Path("benchmarks") / "baselines" / "default.json"


def default_output_path() -> Path:
    """Devuelve la ubicación default del último resultado."""
    return Path("benchmark-results") / "latest.json"


def close_connections() -> None:
    """Cierra conexiones explícitamente al terminar benchmarks internos."""
    global _test_runner, _db_config

    if _test_runner is not None and _db_config is not None:
        _test_runner.teardown_databases(_db_config, verbosity=0)
        _test_runner.teardown_test_environment()
        _test_runner = None
        _db_config = None
    connection.close()
