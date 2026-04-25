from datetime import date

import pytest
from django.db import IntegrityError

from ciudadanos.models import Ciudadano


def test_buscar_por_documento_prefijo_corto_no_ejecuta_query(
    db, django_assert_num_queries
):
    with django_assert_num_queries(0):
        resultados = list(Ciudadano.buscar_por_documento("123456"))

    assert resultados == []


def test_buscar_por_documento_prefijo_siete_digitos_devuelve_coincidencias(db):
    ciudadano_a = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        documento=12345678,
    )
    ciudadano_b = Ciudadano.objects.create(
        nombre="Beto",
        apellido="Lopez",
        fecha_nacimiento=date(1991, 1, 1),
        documento=12345679,
    )
    Ciudadano.objects.create(
        nombre="Caro",
        apellido="Diaz",
        fecha_nacimiento=date(1992, 1, 1),
        documento=99999999,
    )

    resultados = list(Ciudadano.buscar_por_documento("1234567", max_results=10))

    assert [c.pk for c in resultados] == [ciudadano_a.pk, ciudadano_b.pk]


def test_buscar_por_documento_usa_rangos_numericos_indexables(db):
    qs = Ciudadano.buscar_por_documento("1234567", max_results=10)

    sql = str(qs.query).lower()

    assert "like" not in sql
    assert "cast" not in sql
    assert "documento" in sql
    assert ">=" in sql
    assert "<=" in sql


def test_ciudadano_full_clean_acepta_telefono_internacional_formateado(db):
    ciudadano = Ciudadano(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        documento=12345678,
        telefono="+54 9 351 398-9965 interno 1234",
    )

    ciudadano.full_clean()

    assert ciudadano.telefono == "+54 9 351 398-9965 interno 1234"


def test_ciudadano_estandar_setea_documento_unico_key_al_guardar(db):
    ciudadano = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111222,
    )

    assert ciudadano.documento_unico_key == "DNI_30111222"


def test_ciudadano_estandar_no_permite_dni_duplicado(db):
    Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111223,
    )

    with pytest.raises(IntegrityError):
        Ciudadano.objects.create(
            nombre="Beto",
            apellido="Lopez",
            fecha_nacimiento=date(1991, 1, 1),
            tipo_documento=Ciudadano.DOCUMENTO_DNI,
            documento=30111223,
        )


def test_ciudadano_save_update_fields_incluye_clave_derivada(db):
    ciudadano = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111228,
    )

    ciudadano.documento = 30111229
    ciudadano.save(update_fields=["documento"])
    ciudadano.refresh_from_db()

    assert ciudadano.documento_unico_key == "DNI_30111229"


def test_ciudadano_save_update_fields_respeta_revision_manual_explicita(db):
    ciudadano = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111230,
        tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
        motivo_no_validacion_renaper=Ciudadano.MOTIVO_NO_VALIDADO_OTRO,
    )

    ciudadano.requiere_revision_manual = False
    ciudadano.save(update_fields=["requiere_revision_manual"])
    ciudadano.refresh_from_db()

    assert ciudadano.tipo_registro_identidad == Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO
    assert ciudadano.requiere_revision_manual is False


def test_ciudadano_no_validado_permite_dni_duplicado(db):
    for nombre in ("Ana", "Beto"):
        Ciudadano.objects.create(
            nombre=nombre,
            apellido="Perez",
            fecha_nacimiento=date(1990, 1, 1),
            tipo_documento=Ciudadano.DOCUMENTO_DNI,
            documento=30111224,
            tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
            motivo_no_validacion_renaper=Ciudadano.MOTIVO_NO_VALIDADO_OTRO,
        )

    assert Ciudadano.objects.filter(documento=30111224).count() == 2
    assert not Ciudadano.objects.filter(documento=30111224).exclude(
        documento_unico_key__isnull=True
    )


def test_ciudadano_no_validado_permite_mismo_dni_que_estandar(db):
    estandar = Ciudadano.objects.create(
        nombre="Ana",
        apellido="Perez",
        fecha_nacimiento=date(1990, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111225,
    )
    no_validado = Ciudadano.objects.create(
        nombre="Beto",
        apellido="Lopez",
        fecha_nacimiento=date(1991, 1, 1),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=30111225,
        tipo_registro_identidad=Ciudadano.TIPO_REGISTRO_DNI_NO_VALIDADO,
        motivo_no_validacion_renaper=Ciudadano.MOTIVO_NO_VALIDADO_OTRO,
    )

    assert estandar.documento_unico_key == "DNI_30111225"
    assert no_validado.documento_unico_key is None
