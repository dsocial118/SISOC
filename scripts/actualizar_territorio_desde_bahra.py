#!/usr/bin/env python3
"""Incorpora asentamientos BAHRA al fixture territorial sin tocar sus entradas.

El script usa exclusivamente la biblioteca estándar para poder auditar y
reproducir la bajada sin inicializar Django.
"""

import argparse
import csv
import json
import unicodedata
from collections import Counter
from pathlib import Path


MODELO_PROVINCIA = "core.provincia"
MODELO_MUNICIPIO = "core.municipio"
MODELO_LOCALIDAD = "core.localidad"
PK_INICIAL = 100000
PRIORIDAD_CATEGORIA = {
    "Localidad simple": 0,
    "Componente de localidad compuesta": 1,
    "Entidad": 2,
    "Paraje": 3,
}


def norm(valor):
    """Normaliza texto de la misma forma que la comparación del sync."""
    texto = unicodedata.normalize("NFKD", valor or "")
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return " ".join(texto.casefold().split())


def _read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


def _entry(model, pk, **fields):
    return {"model": model, "pk": pk, "fields": fields}


def _candidate_sort_key(row):
    return (
        PRIORIDAD_CATEGORIA[row["categoria"]],
        norm(row["nombre"]),
        row.get("id") or "",
        row["nombre"],
    )


def calcular_actualizacion(fixture_data, asentamientos, municipios):
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Devuelve entradas para append y un resumen, sin escribir en disco."""
    provincias = {
        norm(row["fields"].get("nombre")): row["pk"]
        for row in fixture_data
        if row.get("model") == MODELO_PROVINCIA
    }
    if not provincias:
        raise ValueError("El fixture no contiene provincias.")

    municipios_por_clave = {}
    municipio_provincia = {}
    for row in fixture_data:
        if row.get("model") != MODELO_MUNICIPIO:
            continue
        fields = row["fields"]
        clave = (norm(fields.get("nombre")), fields.get("provincia"))
        municipios_por_clave[clave] = row["pk"]
        municipio_provincia[row["pk"]] = fields.get("provincia")

    localidades_existentes = set()
    localidades_por_provincia = set()
    for row in fixture_data:
        if row.get("model") != MODELO_LOCALIDAD:
            continue
        fields = row["fields"]
        municipio_pk = fields.get("municipio")
        nombre_normalizado = norm(fields.get("nombre"))
        localidades_existentes.add((nombre_normalizado, municipio_pk))
        provincia_pk = municipio_provincia.get(municipio_pk)
        if provincia_pk is not None:
            localidades_por_provincia.add((nombre_normalizado, provincia_pk))

    municipios_planeados = {}

    def provincia_de(row, campo="provincia_nombre"):
        provincia_pk = provincias.get(norm(row.get(campo)))
        if provincia_pk is None:
            raise ValueError(
                "Provincia sin resolver en BAHRA: "
                f"{row.get(campo)!r} ({row.get('nombre')!r})"
            )
        return provincia_pk

    # El CSV de municipios se evalúa completo antes de resolver asentamientos.
    for row in municipios:
        provincia_pk = provincia_de(row)
        nombre = (row.get("nombre") or "").strip()
        clave = (norm(nombre), provincia_pk)
        if not nombre:
            raise ValueError("Municipio BAHRA sin nombre.")
        if clave not in municipios_por_clave:
            anterior = municipios_planeados.get(clave)
            if anterior is None or (norm(nombre), nombre) < (
                norm(anterior["nombre"]),
                anterior["nombre"],
            ):
                municipios_planeados[clave] = {
                    "nombre": nombre,
                    "provincia": provincia_pk,
                    "origen": "oficial",
                }

    # Las localidades se dejan como candidatas hasta asignar los PKs de todos
    # los municipios nuevos, incluidos los pseudo-municipios de departamento.
    candidatas = []
    asentamientos_validos = [
        row
        for row in asentamientos
        if norm((row.get("categoria") or "").strip()) != norm("Base Antartica")
    ]
    for row in sorted(asentamientos_validos, key=_candidate_sort_key):
        categoria = (row.get("categoria") or "").strip()
        if categoria not in PRIORIDAD_CATEGORIA:
            continue
        provincia_pk = provincia_de(row)
        nombre = (row.get("nombre") or "").strip()
        if not nombre:
            raise ValueError(f"Asentamiento BAHRA sin nombre: {row.get('id')!r}")

        municipio_nombre = (row.get("municipio_nombre") or "").strip()
        destino_clave_municipio = (norm(municipio_nombre), provincia_pk)
        municipio_cross_provincia = bool(municipio_nombre) and (
            destino_clave_municipio not in municipios_por_clave
            and destino_clave_municipio not in municipios_planeados
        )
        anclada_a_departamento = not municipio_nombre or municipio_cross_provincia
        destino_nombre = (
            (row.get("departamento_nombre") or "").strip()
            if anclada_a_departamento
            else municipio_nombre
        )
        if not destino_nombre:
            raise ValueError(
                f"Asentamiento sin municipio ni departamento: {row.get('id')!r}"
            )
        destino_clave = (norm(destino_nombre), provincia_pk)

        if (
            destino_clave not in municipios_por_clave
            and destino_clave not in municipios_planeados
        ):
            municipios_planeados[destino_clave] = {
                "nombre": destino_nombre,
                "provincia": provincia_pk,
                "origen": "pseudo_departamento",
            }

        candidatas.append(
            {
                "id": row.get("id") or "",
                "nombre": nombre,
                "nombre_norm": norm(nombre),
                "categoria": categoria,
                "provincia": provincia_pk,
                "destino_clave": destino_clave,
                "anclada_a_departamento": anclada_a_departamento,
                "municipio_cross_provincia": municipio_cross_provincia,
            }
        )

    municipios_nuevos = []
    for pk, (_, definition) in enumerate(
        sorted(
            municipios_planeados.items(),
            key=lambda item: (
                item[1]["provincia"],
                norm(item[1]["nombre"]),
                item[1]["nombre"],
            ),
        ),
        start=PK_INICIAL,
    ):
        definition["pk"] = pk
        municipios_por_clave[_] = pk
        municipio_provincia[pk] = definition["provincia"]
        municipios_nuevos.append(
            _entry(
                MODELO_MUNICIPIO,
                pk,
                nombre=definition["nombre"],
                provincia=definition["provincia"],
            )
        )

    resumen = Counter(
        {
            "asentamientos_fuente": len(asentamientos),
            "bases_antarticas_excluidas": len(asentamientos)
            - len(asentamientos_validos),
            "municipios_oficiales_nuevos": sum(
                item["origen"] == "oficial" for item in municipios_planeados.values()
            ),
            "pseudo_municipios_nuevos": sum(
                item["origen"] == "pseudo_departamento"
                for item in municipios_planeados.values()
            ),
            "municipio_cross_provincia_anclado_a_depto": sum(
                item["municipio_cross_provincia"] for item in candidatas
            ),
        }
    )

    ganadoras = {}
    for candidata in candidatas:
        municipio_pk = municipios_por_clave[candidata["destino_clave"]]
        clave = (candidata["nombre_norm"], municipio_pk)
        if clave in localidades_existentes:
            resumen["descartes_localidad_existente"] += 1
            continue
        if (
            candidata["anclada_a_departamento"]
            and (candidata["nombre_norm"], candidata["provincia"])
            in localidades_por_provincia
        ):
            resumen["descartes_anclaje_anti_duplicado"] += 1
            continue
        if clave in ganadoras:
            resumen["descartes_dedup_interno"] += 1
            continue
        ganadoras[clave] = candidata

    localidades_nuevas = []
    for pk, (_, candidata) in enumerate(
        sorted(
            ganadoras.items(),
            key=lambda item: (
                item[0][1],
                item[1]["nombre_norm"],
                item[1]["nombre"],
                item[1]["id"],
            ),
        ),
        start=PK_INICIAL,
    ):
        municipio_pk = municipios_por_clave[candidata["destino_clave"]]
        localidades_nuevas.append(
            _entry(
                MODELO_LOCALIDAD,
                pk,
                nombre=candidata["nombre"],
                municipio=municipio_pk,
            )
        )
        resumen[f"localidades_{candidata['categoria']}"] += 1

    resumen["municipios_nuevos"] = len(municipios_nuevos)
    resumen["localidades_nuevas"] = len(localidades_nuevas)
    return municipios_nuevos, localidades_nuevas, dict(sorted(resumen.items()))


def actualizar_fixture(
    fixture_path, asentamientos_path, municipios_path, dry_run=False
):
    fixture_path = Path(fixture_path)
    original = fixture_path.read_text(encoding="utf-8")
    fixture_data = json.loads(original)
    serializado_existente = json.dumps(fixture_data, ensure_ascii=False, indent=2)
    if serializado_existente != original:
        raise AssertionError(
            "La serialización de las entradas existentes no reproduce el fixture "
            "byte a byte; se aborta para preservar append-only."
        )

    municipios_nuevos, localidades_nuevas, resumen = calcular_actualizacion(
        fixture_data,
        _read_csv(asentamientos_path),
        _read_csv(municipios_path),
    )
    nuevas_entradas = municipios_nuevos + localidades_nuevas
    if nuevas_entradas and not dry_run:
        serializado_nuevo = json.dumps(nuevas_entradas, ensure_ascii=False, indent=2)
        # Se conserva byte por byte el bloque original de entradas; solo se
        # sustituye el cierre final del array para continuar agregando objetos.
        fixture_path.write_text(
            original[:-2] + ",\n" + serializado_nuevo[2:], encoding="utf-8"
        )
    return resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--asentamientos", required=True)
    parser.add_argument("--municipios", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    resumen = actualizar_fixture(
        args.fixture, args.asentamientos, args.municipios, dry_run=args.dry_run
    )
    for clave, valor in resumen.items():
        print(f"{clave}={valor}")


if __name__ == "__main__":
    main()
