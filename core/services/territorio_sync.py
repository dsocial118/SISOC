"""Sincronización create-only del catálogo territorial desde su fixture."""

import json
import logging
import unicodedata
from pathlib import Path

from django.db import IntegrityError, transaction

from core.models import Localidad, Municipio, Provincia


logger = logging.getLogger(__name__)
FIXTURE_TERRITORIO_PATH = Path("core/fixtures/localidad_municipio_provincia.json")


def normalizar_nombre(valor):
    """Aproxima la comparación ai_ci de MySQL para las claves naturales."""
    texto = unicodedata.normalize("NFKD", valor or "")
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return " ".join(texto.casefold().split())


def _por_clave_natural(instancias, clave):
    """Conserva el primer PK si existen filas orgánicas equivalentes."""
    resultado = {}
    for instancia in instancias:
        resultado.setdefault(clave(instancia), instancia)
    return resultado


def _crear_si_falta(  # pylint: disable=too-many-arguments
    modelo, campos, pk_fixture, pks_ocupados, por_clave, clave, resumen, resumen_key
):
    existente = por_clave.get(clave)
    if existente is not None:
        return existente

    kwargs = dict(campos)
    if pk_fixture not in pks_ocupados:
        kwargs["pk"] = pk_fixture
    try:
        with transaction.atomic():
            instancia = modelo.objects.create(**kwargs)
    except IntegrityError as error:
        # Otra instancia puede haber creado la misma clave entre el prefetch y
        # este insert, o MySQL puede detectar una equivalencia más amplia.
        logger.warning(
            "Territorio no sincronizado para %s(pk_fixture=%s): %s",
            modelo._meta.label,
            pk_fixture,
            error,
        )
        instancia = modelo.objects.filter(**campos).order_by("pk").first()
        if instancia is None:
            return None
        pks_ocupados.add(instancia.pk)
        por_clave[clave] = instancia
        return instancia

    pks_ocupados.add(instancia.pk)
    por_clave[clave] = instancia
    resumen[resumen_key] += 1
    return instancia


def sync_territorio_desde_fixture(path=FIXTURE_TERRITORIO_PATH):
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Crea claves territoriales faltantes sin modificar ni eliminar filas.

    Las tres consultas iniciales permiten que el caso habitual (catálogo ya
    completo) sea solo una comparación en memoria.
    """
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    provincias = list(Provincia.objects.all().order_by("pk"))
    municipios = list(Municipio.objects.all().order_by("pk"))
    localidades = list(Localidad.objects.all().order_by("pk"))
    resumen = {
        "provincias_creadas": 0,
        "municipios_creadas": 0,
        "localidades_creadas": 0,
        "saltadas_por_integridad": 0,
    }

    provincias_por_nombre = _por_clave_natural(
        provincias, lambda provincia: normalizar_nombre(provincia.nombre)
    )
    municipios_por_clave = _por_clave_natural(
        municipios,
        lambda municipio: (normalizar_nombre(municipio.nombre), municipio.provincia_id),
    )
    localidades_por_clave = _por_clave_natural(
        localidades,
        lambda localidad: (normalizar_nombre(localidad.nombre), localidad.municipio_id),
    )
    pks_provincia = {provincia.pk for provincia in provincias}
    pks_municipio = {municipio.pk for municipio in municipios}
    pks_localidad = {localidad.pk for localidad in localidades}
    provincias_fixture = {}
    municipios_fixture = {}

    for entrada in fixture:
        if entrada.get("model") != "core.provincia":
            continue
        nombre = entrada.get("fields", {}).get("nombre") or ""
        clave = normalizar_nombre(nombre)
        provincia = _crear_si_falta(
            Provincia,
            {"nombre": nombre},
            entrada["pk"],
            pks_provincia,
            provincias_por_nombre,
            clave,
            resumen,
            "provincias_creadas",
        )
        if provincia is None:
            resumen["saltadas_por_integridad"] += 1
            provincia = provincias_por_nombre.get(clave)
        if provincia is not None:
            provincias_fixture[entrada["pk"]] = provincia

    for entrada in fixture:
        if entrada.get("model") != "core.municipio":
            continue
        fields = entrada.get("fields", {})
        provincia_fixture_pk = fields.get("provincia")
        provincia = provincias_fixture.get(provincia_fixture_pk)
        if provincia_fixture_pk is not None and provincia is None:
            logger.warning(
                "Municipio omitido: provincia fixture %s no fue resuelta.",
                provincia_fixture_pk,
            )
            resumen["saltadas_por_integridad"] += 1
            continue
        nombre = fields.get("nombre") or ""
        clave = (normalizar_nombre(nombre), provincia.pk if provincia else None)
        municipio = _crear_si_falta(
            Municipio,
            {"nombre": nombre, "provincia": provincia},
            entrada["pk"],
            pks_municipio,
            municipios_por_clave,
            clave,
            resumen,
            "municipios_creadas",
        )
        if municipio is None:
            resumen["saltadas_por_integridad"] += 1
            municipio = municipios_por_clave.get(clave)
        if municipio is not None:
            municipios_fixture[entrada["pk"]] = municipio

    for entrada in fixture:
        if entrada.get("model") != "core.localidad":
            continue
        fields = entrada.get("fields", {})
        municipio_fixture_pk = fields.get("municipio")
        municipio = municipios_fixture.get(municipio_fixture_pk)
        if municipio_fixture_pk is not None and municipio is None:
            logger.warning(
                "Localidad omitida: municipio fixture %s no fue resuelto.",
                municipio_fixture_pk,
            )
            resumen["saltadas_por_integridad"] += 1
            continue
        nombre = fields.get("nombre") or ""
        clave = (normalizar_nombre(nombre), municipio.pk if municipio else None)
        localidad = _crear_si_falta(
            Localidad,
            {"nombre": nombre, "municipio": municipio},
            entrada["pk"],
            pks_localidad,
            localidades_por_clave,
            clave,
            resumen,
            "localidades_creadas",
        )
        if localidad is None:
            resumen["saltadas_por_integridad"] += 1

    return resumen
