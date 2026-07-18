import csv
from datetime import date

import pytest
from django.apps import apps as django_apps

from ciudadanos.models import Ciudadano
from comedores.models import (
    ActividadColaboradorEspacio,
    AuditColaboradorEspacio,
    ColaboradorEspacio,
    Comedor,
    Programas,
)
from comedores.services.pnud_colaboradores_migration import replace_pnud_colaboradores


CSV_HEADERS = [
    "ID Comedor",
    "Apellido",
    "Nombre",
    "DNI",
    "Genero",
    "Telefono",
    "Fecha de Alta",
    "Actividades",
]


def _write_csv(tmp_path, rows):
    csv_path = tmp_path / "colaboradores_pnud.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


@pytest.mark.django_db
def test_replace_pnud_colaboradores_replaces_only_pnud_comedores(tmp_path):
    programa_alimentar, _ = Programas.objects.update_or_create(
        pk=2, defaults={"nombre": "Alimentar comunidad"}
    )
    programa_secos, _ = Programas.objects.update_or_create(
        pk=3, defaults={"nombre": "Abordaje comunitario - Linea Secos"}
    )
    programa_tradicional, _ = Programas.objects.update_or_create(
        pk=4, defaults={"nombre": "Abordaje comunitario - Linea Tradicional"}
    )
    comedor_pnud = Comedor.objects.create(nombre="PNUD", programa=programa_secos)
    comedor_alimentar = Comedor.objects.create(
        nombre="Alimentar", programa=programa_alimentar
    )
    comedor_pnud_sin_csv = Comedor.objects.create(
        nombre="PNUD sin CSV", programa=programa_tradicional
    )
    ciudadano_existente = Ciudadano.objects.create(
        apellido="Existente",
        nombre="Colaborador",
        tipo_documento="DNI",
        documento=11111111,
        sexo=None,
    )
    ciudadano_alimentar = Ciudadano.objects.create(
        apellido="No",
        nombre="Tocar",
        tipo_documento="DNI",
        documento=33333333,
        sexo=None,
    )
    ciudadano_sin_csv = Ciudadano.objects.create(
        apellido="Sin",
        nombre="CSV",
        tipo_documento="DNI",
        documento=55555555,
        sexo=None,
    )
    previo_pnud = ColaboradorEspacio.objects.create(
        comedor=comedor_pnud,
        ciudadano=ciudadano_existente,
        genero="M",
        fecha_alta="2024-01-01",
    )
    previo_alimentar = ColaboradorEspacio.objects.create(
        comedor=comedor_alimentar,
        ciudadano=ciudadano_alimentar,
        genero="M",
        fecha_alta="2024-01-01",
    )
    previo_sin_csv = ColaboradorEspacio.objects.create(
        comedor=comedor_pnud_sin_csv,
        ciudadano=ciudadano_sin_csv,
        genero="M",
        fecha_alta="2024-01-01",
    )
    actividad = ActividadColaboradorEspacio.objects.create(
        alias="CUI",
        nombre="Cuidado Niños/Niñas/Adolesc",
        orden=1,
    )
    csv_path = _write_csv(
        tmp_path,
        [
            {
                "ID Comedor": comedor_pnud.id,
                "Apellido": "Existente",
                "Nombre": "Colaborador",
                "DNI": 11111111,
                "Genero": "???",
                "Telefono": "11-1234567",
                "Fecha de Alta": "2024-02-01",
                "Actividades": "Cuidado Ninos;Ninas;Adolesc",
            },
            {
                "ID Comedor": comedor_pnud.id,
                "Apellido": "Nuevo",
                "Nombre": "Ciudadano",
                "DNI": 22222222,
                "Genero": "Mujer",
                "Telefono": "",
                "Fecha de Alta": "2024-03-01",
                "Actividades": "",
            },
            {
                "ID Comedor": comedor_alimentar.id,
                "Apellido": "No",
                "Nombre": "Tocar",
                "DNI": 33333333,
                "Genero": "Mujer",
                "Telefono": "11-9999999",
                "Fecha de Alta": "2024-03-01",
                "Actividades": "Compras",
            },
            {
                "ID Comedor": 999999999,
                "Apellido": "Inexistente",
                "Nombre": "Comedor",
                "DNI": 44444444,
                "Genero": "Mujer",
                "Telefono": "11-0000000",
                "Fecha de Alta": "2024-03-01",
                "Actividades": "Compras",
            },
        ],
    )

    stats = replace_pnud_colaboradores(
        apps=django_apps,
        csv_path=csv_path,
        run_date=date(2026, 7, 17),
    )

    previo_pnud.refresh_from_db()
    previo_alimentar.refresh_from_db()
    previo_sin_csv.refresh_from_db()
    assert str(previo_pnud.fecha_baja) == "2026-07-17"
    assert previo_alimentar.fecha_baja is None
    assert previo_sin_csv.fecha_baja is None

    nuevos_pnud = ColaboradorEspacio.objects.filter(
        comedor=comedor_pnud, fecha_baja__isnull=True
    ).order_by("ciudadano__documento")
    assert nuevos_pnud.count() == 2
    reutilizado, creado = nuevos_pnud
    assert reutilizado.ciudadano_id == ciudadano_existente.id
    assert reutilizado.genero == "ND"
    assert reutilizado.codigo_telefono == "11"
    assert reutilizado.numero_telefono == "1234567"
    assert list(reutilizado.actividades.values_list("id", flat=True)) == [actividad.id]
    assert creado.ciudadano.documento == 22222222
    assert creado.ciudadano.tipo_documento == "DNI"
    assert creado.ciudadano.sexo is None
    assert creado.codigo_telefono is None
    assert creado.numero_telefono is None
    assert not creado.actividades.exists()
    assert not Ciudadano.objects.filter(documento=44444444).exists()

    assert AuditColaboradorEspacio.objects.filter(
        colaborador=previo_pnud, accion="delete"
    ).exists()
    assert (
        AuditColaboradorEspacio.objects.filter(
            comedor=comedor_pnud, accion="create"
        ).count()
        == 2
    )
    assert stats == {
        "comedores_procesados": 1,
        "comedores_saltados_inexistentes": 1,
        "comedores_saltados_programa": 1,
        "colaboradores_soft_deleteados": 1,
        "colaboradores_creados": 2,
        "ciudadanos_creados": 1,
        "ciudadanos_reutilizados": 1,
        "filas_fallidas": 0,
    }
