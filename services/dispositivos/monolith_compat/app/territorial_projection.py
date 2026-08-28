"""Contrato y aplicación de la proyección territorial de Dispositivos."""

from dataclasses import dataclass
from typing import Iterable

from django.db import transaction

from .models import (
    EstadoProyeccionTerritorial,
    MunicipioTerritorialProyectado,
    ProvinciaTerritorialProyectada,
    VersionProyeccionTerritorial,
)


@dataclass(frozen=True)
class ProvinciaTerritorial:
    source_id: int
    nombre: str


@dataclass(frozen=True)
class MunicipioTerritorial:
    source_id: int
    provincia_source_id: int
    nombre: str


def _records_by_source_id(records: Iterable, record_name: str) -> dict[int, object]:
    indexed = {}
    for record in records:
        if record.source_id in indexed:
            raise ValueError(
                f"{record_name} repetido en la proyección: {record.source_id}"
            )
        indexed[record.source_id] = record
    return indexed


@transaction.atomic
def aplicar_proyeccion_territorial(
    *,
    version: str,
    provincias: Iterable[ProvinciaTerritorial],
    municipios: Iterable[MunicipioTerritorial],
) -> VersionProyeccionTerritorial:
    """Publica una proyección completa y deja intactas las versiones anteriores.

    El llamador debe entregar un snapshot completo con un identificador de versión
    estable. La operación es idempotente para una versión ya publicada y no lee
    ni escribe las tablas territoriales de ``core``.
    """
    version = version.strip()
    if not version:
        raise ValueError("La versión de la proyección territorial es obligatoria.")

    provincias_by_id = _records_by_source_id(provincias, "Provincia")
    municipios_by_id = _records_by_source_id(municipios, "Municipio")

    for municipio in municipios_by_id.values():
        if municipio.provincia_source_id not in provincias_by_id:
            raise ValueError(
                "El municipio proyectado referencia una provincia inexistente: "
                f"{municipio.source_id}"
            )

    snapshot, created = VersionProyeccionTerritorial.objects.get_or_create(
        version=version
    )
    if not created:
        return snapshot

    ProvinciaTerritorialProyectada.objects.bulk_create(
        [
            ProvinciaTerritorialProyectada(
                version=snapshot,
                source_id=provincia.source_id,
                nombre=provincia.nombre,
            )
            for provincia in provincias_by_id.values()
        ]
    )
    provincias_proyectadas = {
        provincia.source_id: provincia
        for provincia in ProvinciaTerritorialProyectada.objects.filter(version=snapshot)
    }
    MunicipioTerritorialProyectado.objects.bulk_create(
        [
            MunicipioTerritorialProyectado(
                version=snapshot,
                source_id=municipio.source_id,
                provincia=provincias_proyectadas[municipio.provincia_source_id],
                nombre=municipio.nombre,
            )
            for municipio in municipios_by_id.values()
        ]
    )
    estado, estado_creado = EstadoProyeccionTerritorial.objects.get_or_create(
        singleton=1,
        defaults={"version": snapshot},
    )
    if not estado_creado and estado.version_id != snapshot.id:
        estado.version = snapshot
        estado.save(update_fields=["version", "actualizado_en"])
    return snapshot
